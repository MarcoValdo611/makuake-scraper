from __future__ import annotations

from dataclasses import dataclass

from lxml import html


@dataclass
class SnapshotMetrics:
    total_amount: int  # 累计销售额（日元）
    total_quantity: int  # 累计销量（件）


# 来自 hero widget 的结构：
# - 集まっている金額 -> /html/body/section/div[2]/div[3]/div[1]/dl/dd
# - サポーター（人数） -> /html/body/section/div[2]/div[3]/div[3]/div[1]/dl/dd
AMOUNT_XPATH = "/html/body/section/div[2]/div[3]/div[1]/dl/dd"
QUANTITY_XPATH = "/html/body/section/div[2]/div[3]/div[3]/div[1]/dl/dd"


def _parse_int_from_text(text: str) -> int:
    # 去掉日文单位、逗号、空格等，只保留数字
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        raise ValueError(f"Cannot parse int from text: {text!r}")
    return int(digits)


def parse_metrics(html_text: str) -> SnapshotMetrics:
    """
    根据固定 XPath 解析出累计销售额与累计销量。
    """
    tree = html.fromstring(html_text)

    amount_nodes = tree.xpath(AMOUNT_XPATH)
    quantity_nodes = tree.xpath(QUANTITY_XPATH)

    if not amount_nodes or not quantity_nodes:
        raise ValueError("XPath did not match expected nodes for amount/quantity.")

    amount_text = "".join(amount_nodes[0].itertext()).strip()
    quantity_text = "".join(quantity_nodes[0].itertext()).strip()

    total_amount = _parse_int_from_text(amount_text)
    total_quantity = _parse_int_from_text(quantity_text)

    return SnapshotMetrics(total_amount=total_amount, total_quantity=total_quantity)

