#most models do this:
(main, aqr, icr liq, misp, q)
except (pa.ArrowIOError, pa.ArrowInvalid) as e:
            msg = f"{self.__class__.__name__}: reading failed: {e}"
            self.log.error(msg)
            raise ValueError(msg) from e


(pa.ArrowIOError, pa.ArrowInvalid)
ArrowInvalid
ValueError
KeyError
(ValueError, TypError)
ImportError (pl, pd)
PackageNotFoundError (cli, version)

httpx.HTTPStatusError
httpx.RequestError

few catchall Exception



# https://github.com/encode/httpx/blob/master/httpx/_exceptions.py
