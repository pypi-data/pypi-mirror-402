# mdsvg2png

A simple Python tool to convert SVG images in Markdown files to PNG format(upload converted .pngs to the Tencent cos).

## Features

- Automatically detects SVG images in Markdown.
- Converts SVG to PNG for better compatibility.
- Easy to use and integrate.

## Config

`.env` or configure environment variables:
```
COS_SECRET_ID=<xyz>
COS_SECRET_KEY=<xyz>
COS_REGION=<xyz>
COS_BUCKET=<xyz>
```

## Usage

1. Install dependencies:
    ```bash
    pip install mdsvg2png
    playwright install
    ```
2. Run the script:
    ```bash
    mdsvg2png your_markdown.md
    ```

## Demo

demo.md:
```
first line

![Version constructor](https://iscinumpy.dev/post/packaging-faster/version.TimeVersionSuite.time_constructor.svg)

end lint
```

demo_output.md
```
first line

![Version constructor](https://pic-1251484506.cos.ap-guangzhou.myqcloud.com/svg2png/version.TimeVersionSuite.time_constructor_3950bb8a.png)

end lint
```

## Note

Depend on playwright to support rendering `<foreignObject>` tag in svg.
TODO: Use resvg_python for static svg.

## License

Apache License