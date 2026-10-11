# Bundled fonts

Both A5/A6 styles load these files by explicit relative path, bypassing system
font discovery. Builds require neither a font installation nor network access.

## Alegreya

`Alegreya-Regular.otf`, `Alegreya-Bold.otf`, and `Alegreya-Italic.otf` are the
unmodified OpenType fonts from Alegreya **2.007**. These are byte-for-byte
identical to the local fonts used for the initial Alegreya previews.

Copyright: © 2011 The Alegreya Project Authors.
Licence: SIL Open Font License 1.1; see [Alegreya-OFL.txt](Alegreya-OFL.txt).
Redistribution and PDF embedding are permitted.

Upstream: https://github.com/huertatipografica/Alegreya/tree/v2.007
Pinned commit: `926acd5a92e2daf7e08c2e04db4c59d73e08cce9`.

To obtain the same files again, run from this directory:

```sh
base=https://raw.githubusercontent.com/huertatipografica/Alegreya/926acd5a92e2daf7e08c2e04db4c59d73e08cce9
for style in Regular Bold Italic; do
  curl --fail --location "$base/fonts/otf/Alegreya-$style.otf" \
    -o "Alegreya-$style.otf"
done
curl --fail --location "$base/OFL.txt" -o Alegreya-OFL.txt
```

SHA-256:

```text
389ff5c3c1a86d6078aa3fa6e3329d5a4ce6dbd28788f2195ed94ce350873765  Alegreya-Regular.otf
bff77aeaacb0a5e5c89f73f77f6d4248766a4aba676d20f6385a29bebbec3442  Alegreya-Bold.otf
8e36f832af0b8a11c8be8e572f273aa7ce9584b0a8fb885ef8918e65cab23c32  Alegreya-Italic.otf
f6f60d5d4cf4f4b1fc4e41353c897a2f5a16e6396c0cd8fa8bdfd2f4586a9a68  Alegreya-OFL.txt
```

## Noto Serif CJK TC

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
