from slidex import Presentation


def main() -> None:
    pres = Presentation.new()
    slide = pres.add_slide()
    slide.add_textbox("Hello from slidex")
    pres.save("generated_minimal.pptx")


if __name__ == "__main__":
    main()
