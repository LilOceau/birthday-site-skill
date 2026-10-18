"""Local static preview with MP4 byte ranges. Serves dist only; loopback by default."""
import argparse
import functools
import http.server
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parent/'dist'

class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        self.remaining=None
        path=pathlib.Path(self.translate_path(self.path)).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            self.send_error(403);return None
        if path.is_dir():path=path/'index.html'
        if not path.is_file():self.send_error(404);return None
        size=path.stat().st_size;start=0;end=size-1
        requested=self.headers.get('Range')
        if requested:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
            if not match or not any(match.groups()):self.send_error(416);return None
            if match[1]:
                start=int(match[1]);end=min(int(match[2]),size-1) if match[2] else size-1
            else:start=max(0,size-int(match[2]))
            if start>end or start>=size:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
        stream=path.open('rb');stream.seek(start);self.remaining=end-start+1
        self.send_response(206 if requested else 200)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Content-Length',str(self.remaining));self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-store')
        if requested:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();return stream

    def copyfile(self,source,outputfile):
        try:
            while self.remaining:
                chunk=source.read(min(65536,self.remaining))
                if not chunk:break
                outputfile.write(chunk);self.remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):pass

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765);parser.add_argument('--bind',default='127.0.0.1')
    args=parser.parse_args()
    server=http.server.ThreadingHTTPServer((args.bind,args.port),functools.partial(Handler,directory=str(ROOT)))
    print(f'Preview: http://{args.bind}:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
