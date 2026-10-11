# Noto Serif CJK TC

`NotoSerifCJKtc-Regular.otf` is the unmodified Traditional Chinese Regular
OpenType font from Noto Serif CJK **2.003**, bundled so book builds need neither
a system font installation nor network access.

Copyright: © 2017–2024 Adobe (http://www.adobe.com/).
Licence: SIL Open Font License 1.1; see [OFL.txt](OFL.txt). Redistribution and
PDF embedding are permitted. Generated PDFs embed only the glyphs they use.

Upstream: https://github.com/notofonts/noto-cjk/tree/Serif2.003/Serif

To obtain the same files again, run from this directory:

```sh
curl --fail --location \
  https://raw.githubusercontent.com/notofonts/noto-cjk/Serif2.003/Serif/OTF/TraditionalChinese/NotoSerifCJKtc-Regular.otf \
  -o NotoSerifCJKtc-Regular.otf
curl --fail --location \
  https://raw.githubusercontent.com/notofonts/noto-cjk/Serif2.003/Serif/LICENSE \
  -o OFL.txt
```

SHA-256:

```text
234301038e76e7c35c43113785024700c4e4fe7bdce1d1fbbc42fca7e6683798  NotoSerifCJKtc-Regular.otf
6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2  OFL.txt
```

The full font is about 24 MB. It covers all four current CJK titles, including
Japanese localized forms selected by `language=jan` in LuaTeX font declarations.
Chinese titles use `language=zht`. The title text is embedded directly in each
book's content `.tex`, not SVG paths or an included title PDF; `玄` in Xuanxuan
Qijing is the character, not the Kangxi radical `⽞` extracted from its old PDF.
Some Japanese localized glyphs extract as canonically equivalent CJK
compatibility ideographs; normalize extracted text to NFC for automated checks.
