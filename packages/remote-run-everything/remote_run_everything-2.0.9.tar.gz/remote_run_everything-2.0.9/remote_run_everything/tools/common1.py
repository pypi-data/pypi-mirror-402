import jinja2, os,base64,struct, glob, arrow, uuid, hashlib


class Common1:

    def clear_by_days(self, root, n):
        files = glob.glob(f"{root}/*/*.*", recursive=True)
        now = arrow.now()
        for f in files:
            info = os.stat(f).st_mtime
            dif = now - arrow.get(info)
            if dif.days > n:
                os.remove(f)

    def str2uuid(self, s):
        hex_string = hashlib.md5(s.encode("UTF-8")).hexdigest()
        return str(uuid.UUID(hex=hex_string))






if __name__ == '__main__':
    g = Common1()
