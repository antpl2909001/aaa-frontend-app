from aiohttp.web import Response
from aiohttp.web import View
from aiohttp_jinja2 import render_template

from lib.image import image_to_img_src
from lib.image import PolygonDrawer
from lib.image import open_image


class IndexView(View):
    async def get(self) -> Response:
        return render_template("index.html", self.request, {})

    async def post(self) -> Response:
        try:
            form = await self.request.post()
            image = open_image(form["image"].file)
            min_thr = float(form["min_thr"]) / 100

            if min_thr < 0 or min_thr > 100:
                raise ValueError(f"Invalid value of min threshold: {min_thr}.\
                                 Must be float from 0 to 100.")

            draw = PolygonDrawer(image)
            model = self.request.app["model"]
            words = []
            for coords, word, confidence in model.readtext(image):
                if confidence >= min_thr:
                    draw.highlight_word(coords, word)
                    cropped_img = draw.crop(coords)
                    cropped_img_b64 = image_to_img_src(cropped_img)
                    words.append(
                        {
                            "image": cropped_img_b64,
                            "text": word,
                            "confidence": confidence,
                        }
                    )
            image_b64 = image_to_img_src(draw.get_highlighted_image())
            ctx = {"image": image_b64, "words": words}
        except Exception as err:
            ctx = {"error": type(err).__name__, "message": str(err)}
        return render_template("index.html", self.request, ctx)
