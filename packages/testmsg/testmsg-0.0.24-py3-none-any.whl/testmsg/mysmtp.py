from typing import Tuple, Union
import smtplib
from rich.console import Console
from rich.text import Text

console = Console()

BytesLike = Union[bytes, bytearray, memoryview]

class MySMTP(smtplib.SMTP):

    _my_verbose: bool = False

    def my_set_verbose(self) -> None:
        self._my_verbose = True        

    def send(self, s: str) -> None:

        if self._my_verbose:
            if isinstance(s, str):
                s_str = s
            else:
                s_str = s.decode(errors="ignore")

            console.print(Text(f">> {s_str.strip()}", style="blue"))

        return super().send(s)

    def getreply(self) -> Tuple[int, BytesLike]:
        code, msg = super().getreply()

        if self._my_verbose:
            # decode safely for printing
            if isinstance(msg, (bytes, bytearray, memoryview)):
                printable = msg.decode(errors="ignore")
            else:
                printable = str(msg)

            # highlight code in green if 2xx, yellow if 3xx, red if 4xx/5xx
            if 200 <= code < 300:
                style = "green"
            elif 300 <= code < 400:
                style = "yellow"
            else:
                style = "red"

            console.print(Text(f"<< {code} {printable}", style=style))

        return code, msg  # type-safe: returns original type

class MySMTP_SSL(MySMTP, smtplib.SMTP_SSL):
    pass
