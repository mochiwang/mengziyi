# 把窗口返回的 JSONL + summary.json 生成规范化 Markdown
# 用法: python tools/make_md.py --lesson-id L123 --date 2025-08-19 --course CS101 \
#        --resdir notes/C_labels --outdir notes/D_markdown
import os, json, argparse

def load_jsonl(p):
    out=[]
    with open(p,"r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line: out.append(json.loads(line))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lesson-id",required=True)
    ap.add_argument("--date",default="")
    ap.add_argument("--course",default="")
    ap.add_argument("--resdir",default="notes/C_labels")
    ap.add_argument("--outdir",default="notes/D_markdown")
    args=ap.parse_args()
    os.makedirs(args.outdir,exist_ok=True)

    jl=os.path.join(args.resdir, f"{args.lesson_id}.jsonl")
    sj=os.path.join(args.resdir, f"{args.lesson_id}.summary.json")
    items=load_jsonl(jl) if os.path.exists(jl) else []
    summary=json.load(open(sj,"r",encoding="utf-8")) if os.path.exists(sj) else {}

    topics=summary.get("topics") or []
    head = [
        "---",
        f"lesson_id: {args.lesson_id}",
        f"date: {args.date}",
        f"course: {args.course}",
        "topics: [" + ", ".join(topics) + "]",
        "---",""
    ]
    lines = head
    lines.append("# 讲义提纲")
    for sec in summary.get("outline", []):
        title = sec.get("title","")
        lines.append(f"- {title}")
        for s in sec.get("subtopics") or []:
            lines.append(f"  - {s}")
    lines.append("")
    lines.append("## 术语表")
    for g in summary.get("glossary", []):
        lines.append(f"- **{g.get('term','')}**：{g.get('brief','')}")
    lines.append("")
    lines.append("## 原文分段")
    for it in items:
        cid = it.get("chunk_id","")
        title = it.get("title","")
        lines.append(f"### {cid} {title}")
        for b in it.get("bullets") or []:
            lines.append(f"- {b}")
        if it.get("zh_explain"):
            lines.append(f"> {it['zh_explain']}")
        lines.append("")
    outp=os.path.join(args.outdir, f"{args.lesson_id}.md")
    with open(outp,"w",encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote", outp)

if __name__=="__main__":
    main()
