from slidex import Presentation


def main() -> None:
    pres = Presentation.open("deck.pptx")
    pres.replace_text("{{quarter}}", "Q1 2026")

    slide = pres.slides[0]
    shape = slide.shapes[0]
    text = shape.as_text()
    text.text = "Hello from slidex"

    pres.save("updated.pptx")


if __name__ == "__main__":
    main()
