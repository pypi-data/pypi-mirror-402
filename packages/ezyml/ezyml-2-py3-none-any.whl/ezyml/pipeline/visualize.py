def render_ascii_dag(nodes, edges):
    lines = []
    for n in nodes:
        children = edges.get(n,[])
        if children:
            lines.append(f"{n} -> {', '.join(children)}")
        else:
            lines.append(n)
    return "\n".join(lines)
