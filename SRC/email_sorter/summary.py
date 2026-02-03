# -*- coding: utf-8 -*-
from collections import defaultdict

def rebuild_summary(wb):
    """
    Rebuilds the Summary sheet from all topic_<domain> sheets.
    Each UpdateGroupKey counts as one 'unique conversation'.
    We also show latest received date per group.
    """
    ws_sum = wb["Summary"]
    ws_sum.delete_rows(1, ws_sum.max_row)
    ws_sum.append([
        "SuperTopicName", "SubTopicName", "TopicID",
        "UniqueConversations", "TotalEmails", "LatestDate"
    ])

    # Load _TopicMap
    ws_map = wb["_TopicMap"]
    topic_name_by_id = {}
    for i, row in enumerate(ws_map.iter_rows(values_only=True), start=1):
        if i == 1:
            continue
        if not row or not row[0]:
            continue
        stid, stname, domain, topic_id, subname = row
        topic_name_by_id[int(topic_id)] = (stname, subname)

    # Aggregate across sheets
    agg = defaultdict(lambda: {"unique": set(), "total": 0, "latest": {}})

    for name in wb.sheetnames:
        if not name.startswith("topic_"):
            continue

        ws = wb[name]
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
        col = {h: i + 1 for i, h in enumerate(header)}

        for r in range(2, ws.max_row + 1):
            topic_id = ws.cell(r, col["TopicID"]).value
            update_key = ws.cell(r, col["UpdateGroupKey"]).value
            received = ws.cell(r, col["Received"]).value

            agg[topic_id]["unique"].add(update_key)
            agg[topic_id]["total"] += 1

            last = agg[topic_id]["latest"].get(update_key)
            if last is None or str(received) > str(last):
                agg[topic_id]["latest"][update_key] = received

    # Write back summary
    for topic_id, data in agg.items():
        stname, subname = topic_name_by_id.get(topic_id, ("", ""))
        latest_date = max((str(v) for v in data["latest"].values()), default="")
        ws_sum.append([
            stname,
            subname,
            topic_id,
            len(data["unique"]),
            data["total"],
            latest_date
        ])

    wb.save(wb.properties.title if wb.properties.title else wb._archive)
