import contextlib
import os
import sys
import threading
from queue import Empty, Queue
from typing import List, Optional, Union

import serial
from serial.tools.miniterm import Console, Miniterm, key_description

from memfault_cli.chunk import MemfaultChunk

"""
Warning: Gross Windows compatibility hack ahead
PySerial maintains compatibility with a wide range of Python and OS versions. Older versions of
Windows originally set the default encoding of stdout/stderr to cp1252. In the Windows
implementation of Console, sys.stdout and stderr are replaced with StreamWriters for utf-8.
However the replacement objects are missing several attributes of the original sys.stdout/err
objects (fileno() and buffer). This yields a bug on Windows if multiple instances of Console
are created.

To work around this, we patch the Console.__init__ method to first restore sys.stdout/err to
their original objects before running the original constructor. This is done using functools.wrap
to pass Console.__init__'s original attributes to the wrapped version. In the wrapped version,
sys.stdout/err are restored before calling the original Console.__init__
"""
if os.name == "nt":
    import functools

    SYS_STDOUT = sys.stdout
    SYS_STDERR = sys.stderr

    def patched_console_init(original_init):
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            sys.stdout = SYS_STDOUT
            sys.stderr = SYS_STDERR
            original_init(self, *args, **kwargs)

        return new_init

    Console.__init__ = patched_console_init(Console.__init__)


class MemfaultConsole(Console):
    """
    Component to read data from stdin and write to outputs (Memfault chunks API and stdout)
    This sublcass parses Memfault chunks from data destined for stdout and sends these to the
    chunk_handler.

    This component spins up a dedicated thread to gather received chunks and send them in a batch.
    The batches are sent when either:
    * The batch size reaches BATCH_MAX
    * The last chunk was received at least CHUNKS_TIMEOUT ago

    Attributes:
        CHUNKS_TIMEOUT: Time in seconds to wait before sending the current batch of chunks
        BATCH_MAX: Maximum number of chunks to batch before sending
    """

    CHUNKS_TIMEOUT = 0.1
    BATCH_MAX = 50

    def __init__(self, chunk_handler: MemfaultChunk, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.line_buffer = bytearray()

        self._lock = threading.RLock()
        self.batch_chunks: List[bytes] = []
        self.process_queue: Queue[List[bytes]] = Queue()
        self.chunk_handler = chunk_handler
        self.worker_thread = threading.Thread(target=self._process_chunks, daemon=True)
        self.last_char: Optional[int] = None
        self.chunks_auto_post = True

    def _under_batch_threshold(self) -> bool:
        """Checks if current batch is below the sending threshold"""
        return len(self.batch_chunks) < self.BATCH_MAX

    def _build_batch(self) -> bool:
        """Checks if a batch should be built or sent"""
        return not self.batch_chunks or self._under_batch_threshold()

    def _process_chunks(self) -> None:
        """Thread target to process chunks written to the console"""
        while True:
            while self._build_batch():
                # Set a timeout if chunks in batch or no timeout if starting new batch
                timeout = self.CHUNKS_TIMEOUT if self.batch_chunks else None
                try:
                    next_chunk = self.process_queue.get(timeout=timeout)
                except Empty:
                    break
                else:
                    self.batch_chunks.extend(next_chunk)
                    continue

            if self.batch_chunks and self.chunks_auto_post:
                self._console_write_line(
                    f"Sending {len(self.batch_chunks)} chunks to Memfault cloud"
                )
                self.chunk_handler.batch_post(self.batch_chunks)
                self._console_write_line("Success")
                self.batch_chunks = []
                self.byte_output.flush()

    def _write(self, data_buffer: Union[bytes, bytearray]) -> int:
        """Helper function to write data to stdout. Returns number of bytes written. Acquires
        internal lock for thread-safety"""
        with self._lock:
            self.last_char = data_buffer[-1]
            return self.byte_output.write(data_buffer)  # pyright: ignore[reportArgumentType, reportReturnType]

    def _console_write_line(self, msg: str) -> None:
        """Helper function write to stdout, uses configured line endings. Acquires internal lock"""
        with self._lock:
            prefix = "\r\n" if self.last_char != ord("\n") else ""
            self._write(f"{prefix}[MFLT CONSOLE]: {msg}\r\n".encode())
            self.byte_output.flush()

    def write_bytes(self, byte_string: bytes) -> None:
        """
        External interface for writing to console output (stdout) and sending to the chunk_handler.

        Each byte is written to stdout, then checked if it is a newline. If a newline is
        encountered, any chunks in the current line are extracted. Processed chunk data is sent to
        _process_chunks via a Queue. All bytes are echoed to stdout.
        """
        for b in byte_string:
            self._write(bytes([b]))
            self.line_buffer.append(b)

            if b != ord("\n"):
                continue

            #
            # We have hit the end of a line -- run analyzers
            #
            line = self.line_buffer.decode("utf-8", errors="replace")
            self.line_buffer = bytearray()

            if self.chunk_handler:
                chunks = self.chunk_handler.extract_exported_chunks(line)
                if chunks:
                    self.process_queue.put(chunks)

        self.byte_output.flush()

    def start(self) -> None:
        """Starts the MemfaultConsole worker. Can be called multiple times safely"""
        if not self.worker_thread.is_alive():
            self.worker_thread.start()


class MemfaultMiniterm(Miniterm):
    """
    Reads data from a serial port and forwards to MemfaultConsole component. The console is
    responsible for parsing Memfault chunks from the serial input and passing to the chunk handler.
    Configured specifically for use with Memfault CLI console.

    Attributes:
        CHUNKS_AUTO_POST_KEY: String value of the key to toggle the chunks auto post setting
        console: Used as bridge between serial input at stdout
    """

    CHUNKS_AUTO_POST_KEY = "c"

    console: MemfaultConsole

    def __init__(self, serial_instance, chunk_handler: MemfaultChunk, *args, **kwargs) -> None:
        super().__init__(serial_instance, *args, **kwargs)
        self.console = MemfaultConsole(chunk_handler)
        self.set_rx_encoding("UTF-8")
        self.set_tx_encoding("UTF-8")
        self.raw = True

    def handle_menu_key(self, c: str) -> None:
        """Override adding MemfaultTerminal specific menu key handling"""
        # Check for chunks specific command first, then hand off to super
        if c == self.CHUNKS_AUTO_POST_KEY:
            self.console.chunks_auto_post = not self.console.chunks_auto_post
            self.dump_port_settings()
            return None
        else:
            return super().handle_menu_key(c)

    def _get_memfault_help_text(self) -> str:
        """
        Returns the help text for Memfault specific options

        Returns:
            str: Help text to append to super().get_help_text
        """
        return f"""
--- Memfault Options ({key_description(self.menu_character)} followed by the following):
---    c Toggle automatic chunk collecting and posting to Memfault
        """

    def get_help_text(self) -> str:
        """Overrides to append MemfaultMiniterm help text"""
        memfault_help_text = self._get_memfault_help_text()
        base_text = super().get_help_text()
        return "".join([base_text, memfault_help_text])

    def _dump_memfault_settings(self) -> str:
        return (
            f"--- chunks auto-post: {'active' if self.console.chunks_auto_post else 'inactive'}\n"
        )

    def dump_port_settings(self) -> None:
        """Overrides to append Memfault settings to output"""
        super().dump_port_settings()
        sys.stderr.write("--- Memfault Settings:\n")
        sys.stderr.write(self._dump_memfault_settings())

    def start(self) -> None:
        """Starts all threads required for operation. Save to call repeatedly"""
        self.console.start()
        if not self.alive:
            super().start()

    @staticmethod
    def from_port(port: str, chunk_handler: MemfaultChunk, baudrate=115200) -> None:
        """
        Create and start a new instance of MemfaultMiniterm using the provided serial port.

        Runs until Miniterm is closed by the user.

        Args:
            port (str): String as a path or URL to create a Serial instance
            chunk_handler (MemfaultChunk): Handles sending chunks via Memfault /chunks API
            baudrate (int): Baudrate to use with underlying serial port
        """
        serial_instance = serial.serial_for_url(
            port,
            baudrate,
            parity="N",
            rtscts=False,
            xonxoff=False,
            exclusive=True,
            do_not_open=True,
        )
        serial_instance.open()

        miniterm = MemfaultMiniterm(
            serial_instance,
            chunk_handler,
            echo=False,
            eol="crlf",
            filters=["default"],
        )

        sys.stderr.write(
            f"\r\n--- Memfault Console on {miniterm.serial.name}  {miniterm.serial.baudrate},{miniterm.serial.bytesize},{miniterm.serial.parity},{miniterm.serial.stopbits} ---\n"
        )
        sys.stderr.write(
            "--- Quit: {} | Menu: {} | Help: {} followed by {} ---\n".format(
                key_description(miniterm.exit_character),
                key_description(miniterm.menu_character),
                key_description(miniterm.menu_character),
                key_description("\x08"),
            )
        )

        miniterm.start()
        with contextlib.suppress(KeyboardInterrupt):
            miniterm.join(True)

        sys.stderr.write("\r\n--- Exiting Memfault Console ---\r\n")
        miniterm.join()
        miniterm.close()
