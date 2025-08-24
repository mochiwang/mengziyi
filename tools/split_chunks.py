# 智能切块：按段落与句子边界把 .txt 分成 ~1200 字的小块
# 用法: python tools/split_chunks.py <txt_path> --lesson-id L123 --max-chars 1200 --outdir notes/B_chunks
import os, re, argparse, json

def smart_split(text, max_chars=1200):
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, buf = [], ""
    def flush():
        nonlocal buf
        if buf.strip(): chunks.append(buf.strip()); buf = ""
    for p in paras:
        if len(buf) + len(p) + 1 <= max_chars:
            buf += ("\n" + p) if buf else p
        else:
            if not buf and len(p) > max_chars:
                # 句子再切
                sents = re.split(r'(?<=[。.!?？])\s+', p)
                cur = ""
                for s in sents:
                    if len(cur) + len(s) + 1 <= max_chars:
                        cur += (s if not cur else " " + s)
                    else:
                        if cur: chunks.append(cur.strip()); cur = s
                if cur: chunks.append(cur.strip())
            else:
                flush(); buf = p
    flush()
    return chunks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--lesson-id", required=True)
    ap.add_argument("--max-chars", type=int, default=1200)
    ap.add_argument("--outdir", default="notes/B_chunks")
    args = ap.parse_args()

    with open(args.path, "r", encoding="utf-8") as f: text = f.read()
    os.makedirs(args.outdir, exist_ok=True)
    chunks = smart_split(text, args.max_chars)
    idx = {"lesson_id": args.lesson_id, "chunks": []}
    for i, c in enumerate(chunks, 1):
        cid = f"{args.lesson_id}-{i:04d}"
        outp = os.path.join(args.outdir, f"{cid}.txt")
        with open(outp, "w", encoding="utf-8") as f: f.write(c)
        idx["chunks"].append({"chunk_id": cid, "file": outp, "chars": len(c)})
    indexp = os.path.join(args.outdir, f"{args.lesson_id}.index.json")
    with open(indexp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    print(f"Made {len(chunks)} chunks at {args.outdir}, index -> {indexp}")

if __name__ == "__main__":
    main()
