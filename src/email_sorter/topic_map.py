# -*- coding: utf-8 -*-
from openpyxl.worksheet.worksheet import Worksheet

class TopicMap:
    """
    Maintains the _TopicMap sheet with the schema:
      SuperTopicID | SuperTopicName | Domain | TopicID | SubTopicName

    - SuperTopicID corresponds to a company/domain cluster ID.
    - TopicID = SuperTopicID * 100 + SubTopicIndex.
    - Users may freely rename SuperTopicName and SubTopicName in Excel.
    """

    def _read_all(self, ws: Worksheet):
        """Read all data rows from the _TopicMap sheet, skipping the header and blank rows."""
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
        Ensure that rows exist for (domain, subtopic_index).

        Returns a dict with topic metadata:
          {
            "SuperTopicID": int,
            "SuperTopicName": str,
            "TopicID": int,
            "SubTopicName": str,
            "Domain": str
          }
        """
        ws = wb["_TopicMap"]
        existing = self._read_all(ws)

        # Find the existing SuperTopicID for this domain, if any
        domain_entries = [r for r in existing if r[2] == domain]
        if domain_entries:
            super_topic_id = int(domain_entries[0][0])
            super_topic_name = domain_entries[0][1] or domain
        else:
            # Assign a new SuperTopicID
            max_id = max([int(r[0]) for r in existing], default=1)
            super_topic_id = max_id + 1
            super_topic_name = domain

            # Add a default "General" subtopic (index 0)
            topic_id0 = super_topic_id * 100 + 0
            ws.append([super_topic_id, super_topic_name, domain, topic_id0, "General"])

        # Compute the TopicID for the requested subtopic
        topic_id = super_topic_id * 100 + subtopic_index

        # Ensure the specific subtopic row exists
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
