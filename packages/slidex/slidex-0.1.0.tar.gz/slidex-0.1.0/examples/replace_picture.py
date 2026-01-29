from slidex import Presentation


def main() -> None:
    pres = Presentation.open("deck.pptx")
    image_bytes = open("image.png", "rb").read()

    picture = pres.slides[0].shapes.find(type="picture")[0].as_picture()
    picture.replace(image_bytes)

    pres.save("deck_out.pptx")


if __name__ == "__main__":
    main()
