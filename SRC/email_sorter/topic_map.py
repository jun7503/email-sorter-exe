# -*- coding: utf-8 -*-
from openpyxl.worksheet.worksheet import Worksheet

class TopicMap:
    """
    Maintains _TopicMap sheet:
      SuperTopicID | SuperTopicName | Domain | TopicID | SubTopicName

    - SuperTopicID corresponds to company/domain cluster ID.
    - TopicID = SuperTopicID * 100 + SubTopicIndex.
    - Users may rename SuperTopicName and SubTopicName freely in Excel.
    """

    def _read_all(self, ws: Worksheet):
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i == 1:
                continue
            if not row or not row[0]:
                continue
            rows.append(row)
        return rows

    def ensure_domain_topic(self, wb, domain: str, subtopic_index: int):
        """
        Ensure rows exist for (domain, subtopic_index).
        Returns dict with topic metadata:
          { SuperTopicID, SuperTopicName, TopicID, SubTopicName, Domain }
        """
        ws = wb["_TopicMap"]
        existing = self._read_all(ws)

        # Find existing SuperTopicID for this domain
        domain_entries = [r for r in existing if r[2] == domain]
        if domain_entries:
            super_topic_id = int(domain_entries[0][0])
            super_topic_name = domain_entries[0][1] or domain
        else:
            # Assign new SuperTopicID
            max_id = max([int(r[0]) for r in existing], default=1)
            super_topic_id = max_id + 1
            super_topic_name = domain

            # Add "General" (subtopic 0)
            topic_id0 = super_topic_id * 100 + 0
            ws.append([super_topic_id, super_topic_name, domain, topic_id0, "General"])

        # Derive TopicID
        topic_id = super_topic_id * 100 + subtopic_index

        # Ensure specific subtopic row exists
        found = [r for r in existing if int(r[3]) == topic_id]
        if not found:
            ws.append([super_topic_id, super_topic_name, domain, topic_id, f"Topic {topic_id}"])

        return {
            "SuperTopicID": super_topic_id,
            "SuperTopicName": super_topic_name,
            "TopicID": topic_id,
            "SubTopicName": f"Topic {topic_id}",
            "Domain": domain
        }
