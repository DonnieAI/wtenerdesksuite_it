from __future__ import annotations
from pathlib import Path
from lxml import etree
from typing import Dict, Optional, List
from dataclasses import dataclass
import pandas as pd 





def get_law_metadata(xml_path: Path) -> Dict[str, Optional[str]]:
    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    # AKN default namespace
    akn_ns = root.nsmap.get(None)
    if not akn_ns:
        raise ValueError("No default namespace found (not Akoma Ntoso?)")

    # Namespaces for XPath
    ns = {
        "akn": akn_ns,
        # these may exist in your file; we include them if present
        "nrdfa": root.nsmap.get("nrdfa", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0/nrdfa"),
    }

    def x_string(xpath_expr: str) -> Optional[str]:
        s = root.xpath(f"string({xpath_expr})", namespaces=ns)
        s = " ".join(s.split())
        return s or None

    def x_first_attr(xpath_expr: str) -> Optional[str]:
        vals = root.xpath(xpath_expr, namespaces=ns)
        return vals[0] if vals else None

    # Basic visible title
    doc_title = x_string(".//akn:docTitle")

    # FRBR core
    frbr_work_date = x_first_attr(".//akn:FRBRWork/akn:FRBRdate/@date")
    frbr_this = x_first_attr(".//akn:FRBRWork/akn:FRBRthis/@value")
    frbr_uri = x_first_attr(".//akn:FRBRWork/akn:FRBRuri/@value")

    # Aliases
    nir_urn = x_first_attr(".//akn:FRBRWork/akn:FRBRalias[@name='urn:nir']/@value")
    eli_alias = x_first_attr(".//akn:FRBRWork/akn:FRBRalias[@name='eli']/@value")

    # ELI / RDFa enrichment (Normattiva-style)
    eli_id_local = x_first_attr(".//nrdfa:span[@property='eli:id_local']/@content")
    eli_title = x_first_attr(".//nrdfa:span[@property='eli:title']/@content")

    return {
        "doc_title": doc_title,
        "frbr_date": frbr_work_date,
        "frbr_this": frbr_this,
        "frbr_uri": frbr_uri,
        "nir_urn": nir_urn,
        "eli_alias": eli_alias,
        "eli_id_local": eli_id_local,   # e.g. 26G00041
        "eli_title": eli_title,         # often includes (26G00041)
    }


# -------------------------
# Helpers (lxml)
# -------------------------
def extract_namespace(root: etree._Element) -> Dict[str, str]:
    """Bind detected default namespace to prefix 'akn'."""
    ns_uri = root.nsmap.get(None)
    if not ns_uri:
        raise ValueError("No default namespace found (not Akoma Ntoso?)")
    return {"akn": ns_uri}


def clean_ws(s: str) -> str:
    return " ".join(s.split())


# -------------------------
# Extraction
# -------------------------
def extract_preamble_citations(xml_path: Path) -> List[Dict]:
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    ns = extract_namespace(root)

    # find preamble
    preamble_nodes = root.xpath(".//akn:preamble", namespaces=ns)
    if not preamble_nodes:
        return []
    preamble = preamble_nodes[0]

    citations_output: List[Dict] = []

    # all citations inside preamble
    for citation in preamble.xpath(".//akn:citation", namespaces=ns):
        citation_eid = citation.get("eId")

        # full visible text (including inner ref text)
        full_text = clean_ws("".join(citation.itertext()))

        references = []
        for ref in citation.xpath(".//akn:ref", namespaces=ns):
            references.append({
                "ref_eId": ref.get("eId"),
                "href": ref.get("href"),
                "text": clean_ws("".join(ref.itertext()))
            })

        citations_output.append({
            "citation_eId": citation_eid,
            "text": full_text,
            "references": references
        })

    return citations_output


@dataclass
class ArticleInfo:
    eId: Optional[str]
    article_number: Optional[str]
    title: Optional[str]


def list_articles_with_titles(xml_path: Path) -> List[ArticleInfo]:

    tree = etree.parse(str(xml_path))
    root = tree.getroot()

    # auto-detect default namespace
    ns_uri = root.nsmap.get(None)
    if not ns_uri:
        raise ValueError("No default namespace found (not Akoma Ntoso?)")

    ns = {"akn": ns_uri}

    articles_data: List[ArticleInfo] = []

    # XPath instead of findall
    for article in root.xpath(".//akn:article", namespaces=ns):

        eid = article.get("eId")

        # string() safely concatenates nested text if needed
        article_number = article.xpath("string(akn:num)", namespaces=ns).strip() or None
        title = article.xpath("string(akn:heading)", namespaces=ns).strip() or None

        articles_data.append(
            ArticleInfo(
                eId=eid,
                article_number=article_number,
                title=title
            )
        )

    return articles_data

# -------------------------
# Helpers (lxml)
# -------------------------
def extract_namespace(root: etree._Element) -> Dict[str, str]:
    """Bind detected default namespace to prefix 'akn'."""
    ns_uri = root.nsmap.get(None)
    if not ns_uri:
        raise ValueError("No default namespace found (not Akoma Ntoso?)")
    return {"akn": ns_uri}

def local_name(tag: str) -> str:
    """Strip namespace: '{uri}tag' -> 'tag'."""
    return etree.QName(tag).localname if tag else ""

def clean_ws(s: str) -> str:
    return " ".join(s.split())

def text_of(el: Optional[etree._Element]) -> str:
    if el is None:
        return ""
    return clean_ws("".join(el.itertext()))


def first(node: etree._Element, xpath_expr: str, ns: Dict[str, str]) -> Optional[etree._Element]:
    hits = node.xpath(xpath_expr, namespaces=ns)
    return hits[0] if hits else None


def all_(node: etree._Element, xpath_expr: str, ns: Dict[str, str]) -> List[etree._Element]:
    return node.xpath(xpath_expr, namespaces=ns)


# -------------------------
# Data model
# -------------------------
@dataclass
class Block:
    kind: str               # "paragraph" | "item" | "text"
    num: str                # "1." / "a)" / etc (may be empty)
    text: str               # the actual content


@dataclass
class ArticleContent:
    eId: str
    article_number: str
    title: str
    blocks: List[Block]


# -------------------------
# Extraction (lxml + XPath)
# -------------------------
def find_article_element(root: etree._Element, ns: Dict[str, str], article_eid: str) -> etree._Element:
    hits = root.xpath(f".//akn:article[@eId='{article_eid}']", namespaces=ns)
    if not hits:
        raise ValueError(f"Article with eId='{article_eid}' not found.")
    return hits[0]


def extract_article_content(xml_path: Path, article_eid: str) -> ArticleContent:
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    ns = extract_namespace(root)

    article = find_article_element(root, ns, article_eid)

    # Header
    art_num = text_of(first(article, "./akn:num", ns))
    heading = text_of(first(article, "./akn:heading", ns))

    blocks: List[Block] = []

    # Walk DIRECT children of <article> to preserve order
    for child in list(article):
        cname = local_name(child.tag)

        # 1) <paragraph> ... </paragraph>
        if cname == "paragraph":
            p_num = text_of(first(child, "./akn:num", ns))

            # paragraph <p> text
            ps = all_(child, ".//akn:p", ns)
            if ps:
                for i, p in enumerate(ps):
                    blocks.append(Block(
                        kind="paragraph",
                        num=p_num if i == 0 else "",
                        text=text_of(p)
                    ))
            else:
                blocks.append(Block(kind="paragraph", num=p_num, text=text_of(child)))

            # ALSO capture blockList items inside the paragraph (common in Italian laws)
            items = all_(child, ".//akn:blockList/akn:item", ns)
            for item in items:
                i_num = text_of(first(item, "./akn:num", ns))
                item_ps = all_(item, ".//akn:p", ns)
                if item_ps:
                    for j, p in enumerate(item_ps):
                        blocks.append(Block(kind="item", num=i_num if j == 0 else "", text=text_of(p)))
                else:
                    blocks.append(Block(kind="item", num=i_num, text=text_of(item)))

        # 2) <blockList> directly under article
        elif cname == "blockList":
            for item in all_(child, "./akn:item", ns):
                i_num = text_of(first(item, "./akn:num", ns))
                ps = all_(item, ".//akn:p", ns)
                if ps:
                    for j, p in enumerate(ps):
                        blocks.append(Block(kind="item", num=i_num if j == 0 else "", text=text_of(p)))
                else:
                    blocks.append(Block(kind="item", num=i_num, text=text_of(item)))

        # 3) Sometimes text is directly under article as <p>
        elif cname == "p":
            blocks.append(Block(kind="text", num="", text=text_of(child)))

        # 4) Ignore header nodes already captured
        elif cname in {"num", "heading"}:
            continue

        else:
            # Conservative fallback: include <p> from this subtree as plain text
            ps = all_(child, ".//akn:p", ns)
            for p in ps:
                blocks.append(Block(kind="text", num="", text=text_of(p)))

    return ArticleContent(
        eId=article_eid,
        article_number=art_num,
        title=heading,
        blocks=[b for b in blocks if b.text]
    )


# -------------------------
# Markdown rendering (unchanged)
# -------------------------
def render_article_markdown(article: ArticleContent) -> str:
    md = ""
    if article.article_number:
        md += f"## {article.article_number}\n\n"
    if article.title:
        md += f"**{article.title}**\n\n"

    for b in article.blocks:
        if b.kind == "paragraph":
            md += f"**{b.num}** {b.text}\n\n" if b.num else f"{b.text}\n\n"
        elif b.kind == "item":
            md += f"- **{b.num}** {b.text}\n" if b.num else f"- {b.text}\n"
        else:
            md += f"{b.text}\n\n"

    return md.strip() + "\n"