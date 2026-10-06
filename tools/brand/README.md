# Rebuilding the brand images

You only need this to change the logo or the marketing images in `assets/brand/`. The skill and plugin don't depend on it.

1. `pip install -r tools/brand/requirements.txt`
2. Download Poppins (SIL Open Font License) from [Google Fonts](https://fonts.google.com/specimen/Poppins) and put `Poppins-Bold.ttf`, `Poppins-Medium.ttf`, and `Poppins-Regular.ttf` in `tools/brand/fonts/` (or point `POPPINS_DIR` at a folder that has them).
3. `python3 tools/brand/build_logo.py` rebuilds the mark, wordmark, lockups, icons, and banners.
4. `python3 tools/brand/marketing.py` rebuilds the README images.

Every output is outlined paths, so nobody viewing them needs the font. Rebuilding with the same font files produces byte-identical output.
