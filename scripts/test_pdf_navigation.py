#!/usr/bin/env python3
"""Exercise the shared Plain TeX PDF navigation with optional build tools."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


BOOKS = Path(__file__).resolve().parent.parent / "books"


@unittest.skipUnless(
    shutil.which("luatex") and shutil.which("mutool"),
    "PDF navigation tests need luatex and mutool",
)
class PdfNavigationTests(unittest.TestCase):
    def test_labels_and_bookmarks(self) -> None:
        # A5 usually has two preliminary pages; longer A6 introductions have
        # three. Test both independently of the Go fonts and diagram layout.
        for front_pages in (2, 3):
            for sectioned in (False, True):
                with self.subTest(front_pages=front_pages, sectioned=sectioned):
                    self.check_navigation(front_pages, sectioned)

    def check_navigation(self, front_pages: int, sectioned: bool) -> None:
        tex = [
            r"\input luatex85.sty",
            r"\input includes/pdf-navigation",
        ]
        if sectioned:
            tex.extend([
                r"\pdfsectionbookmark{1}{Living}",
                r"\pdfsectionbookmark{2}{Killing}",
            ])
        tex.extend([r"\null\vfill\eject"] * front_pages)
        tex.extend([
            r"\problempagelabels",
            r"\pageno=1",
            r"\pdfdest name {problem-1-1} xyz",
            r"\noindent First problem.\vfill\eject",
            r"\pdfdest name {problem-2-1} xyz",
            r"\noindent Second problem.\bye",
        ])
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "navigation.tex"
            source.write_text("\n".join(tex) + "\n")
            build = subprocess.run(
                ["luatex", "-no-shell-escape", "-interaction=nonstopmode",
                 "-halt-on-error", f"-output-directory={directory}", str(source)],
                cwd=BOOKS, capture_output=True, text=True,
            )
            self.assertEqual(0, build.returncode, build.stdout + build.stderr)
            pdf = source.with_suffix(".pdf")

            def show(key: str) -> str:
                return subprocess.check_output(
                    ["mutool", "show", str(pdf), key], text=True,
                )

            labels = " ".join(show("trailer/Root/PageLabels").split())
            self.assertEqual(
                f"<< /Nums [ 0 << /S /r >> {front_pages} "
                "<< /S /D /St 1 >> ] >>",
                labels,
            )
            outline = show("outline")
            self.assertIn('"Title"\t#page=1&view=Fit', outline)
            self.assertIn('"Preface"\t#page=2&view=Fit', outline)
            if sectioned:
                self.assertEqual(4, len(outline.splitlines()))
                for chapter, title in ((1, "Living"), (2, "Killing")):
                    self.assertIn(
                        f'"{chapter}. {title}"\t#nameddest=problem-{chapter}-1',
                        outline,
                    )
                # Both named destinations must be defined, not just referenced.
                names = show("trailer/Root/Names/Dests/Names")
                for chapter in (1, 2):
                    self.assertRegex(names, rf"\(problem-{chapter}-1\) \d+ 0 R")
            else:
                self.assertEqual(3, len(outline.splitlines()))
                self.assertIn(
                    f'"Problems"\t#page={front_pages + 1}&view=Fit', outline,
                )


if __name__ == "__main__":
    unittest.main()
