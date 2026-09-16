#!/usr/bin/env python3
"""Build the email-safe table and raster slices from one editable profile.

Usage: python3 scripts/build_signature.py 'EMMA L'
Requires Pillow. Original GIF timing, typewriter sequence and loop are retained.
"""
import argparse
import html
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
BG = (35, 35, 35)
ORIGINAL = dict(first_name='Emma', last_name='LAHOREAU', role='Cheffe de projet',
                phone_display='07 63 47 52 05')
FIELDS = {
    'first_name': ((30, 130, 650, 271), 111, 'name'),
    'last_name': ((30, 272, 650, 412), 111, 'name'),
    'role': ((30, 420, 550, 500), 46, 'detail'),
    'phone_display': ((30, 501, 550, 589), 46, 'detail'),
}


def font_for(config, kind, size):
    custom = config.get(kind + '_font')
    candidates = [custom] if custom else (
        ['/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf',
         '/usr/share/fonts/truetype/liberation2/LiberationSerif-Italic.ttf']
        if kind == 'name' else
        ['/System/Library/Fonts/HelveticaNeue.ttc',
         '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'])
    for filename in candidates:
        if filename and Path(filename).is_file():
            return ImageFont.truetype(filename, size)
    raise RuntimeError('Renseignez ' + kind + '_font dans signature.json avec un chemin de police TTF/OTF.')


def make_left(folder, config, reference):
    left = reference.crop((0, 0, 1296, 632))
    # Extract the already-cut-out portrait from the approved mockup, without
    # regenerating the face or hair. Original photograph is kept alongside it.
    portrait_path = folder / 'source/portrait.png'
    if not portrait_path.exists():
        portrait = left.crop((555, 0, 1296, 632))
        ImageDraw.Draw(portrait).rectangle((0, 120, 94, 411), fill=BG)
        portrait.save(portrait_path)
    photo_path = folder / config['photo_cutout']
    if photo_path.resolve() != portrait_path.resolve():
        photo = Image.open(photo_path).convert('RGBA')
        area = (555, 0, 1296, 632)
        ImageDraw.Draw(left).rectangle(area, fill=BG)
        ratio = min(741 / photo.width, 632 / photo.height)
        photo = photo.resize((round(photo.width * ratio), round(photo.height * ratio)), Image.Resampling.LANCZOS)
        left.paste(photo, (555 + (741 - photo.width) // 2, 632 - photo.height), photo)
        # Restore any typography that extends into the portrait column.
        for key in ('first_name', 'last_name'):
            box = FIELDS[key][0]
            left.paste(reference.crop(box), box[:2])
    draw = ImageDraw.Draw(left)
    for key, (box, size, kind) in FIELDS.items():
        if config[key] == ORIGINAL[key]:
            continue
        draw.rectangle(box, fill=BG)
        font = font_for(config, kind, size)
        while draw.textbbox((0, 0), config[key], font=font)[2] > box[2] - box[0] - 12 and size > 12:
            size -= 1
            font = font_for(config, kind, size)
        bounds = draw.textbbox((0, 0), config[key], font=font)
        top = box[1] + (box[3] - box[1] - (bounds[3] - bounds[1])) // 2
        draw.text((40 - bounds[0], top - bounds[1]), config[key], font=font, fill='white')
    return left


def make_animation(reference, dest):
    source = Image.open(ROOT / 'impact-makers.gif')
    base = reference.crop((1296, 0, 1924, 632))
    # The reference supplies the exact WE ARE / MAKERS lettering. Only the
    # animated middle line is replaced, using every original frame in order.
    ImageDraw.Draw(base).rectangle((0, 237, 627, 389), fill='white')
    frames, durations = [], []
    for frame in ImageSequence.Iterator(source):
        middle = frame.convert('RGB').crop((0, 240, 360, 340))
        middle = middle.point(lambda value: round(35 + value * 220 / 255))
        middle = middle.resize((803, 200), Image.Resampling.LANCZOS)
        panel = base.copy()
        panel.paste(middle, (-80, 219))
        panel = panel.resize((294, 296), Image.Resampling.LANCZOS)
        frames.append(panel.convert('L').convert('P'))
        durations.append(frame.info.get('duration', 100))
    frames[0].save(dest, save_all=True, append_images=frames[1:], duration=durations,
                   loop=source.info.get('loop', 0), disposal=1, optimize=True)
    return frames[0].convert('RGB'), durations


def email_table(config, base):
    e = html.escape
    def img(name, width, height, alt=''):
        return (f'<img src="{e(base + name, quote=True)}" width="{width}" height="{height}" '
                f'alt="{e(alt, quote=True)}" border="0" style="display:block;border:0;outline:none;'
                f'text-decoration:none;width:{width}px;height:{height}px;max-width:none;">')
    label = f"{config['first_name']} {config['last_name']} — {config['role']} — ANEKDOTE × DBM"
    td = 'padding:0;margin:0;font-size:0;line-height:0;vertical-align:top;'
    return f'''<!-- Signature 450 × 148 px. Seul le numéro est cliquable. -->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="450" style="width:450px;border-collapse:collapse;border-spacing:0;table-layout:fixed;mso-table-lspace:0pt;mso-table-rspace:0pt;">
  <tr>
    <td width="303" height="148" bgcolor="#232323" style="{td}width:303px;height:148px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="303" style="width:303px;border-collapse:collapse;border-spacing:0;mso-table-lspace:0pt;mso-table-rspace:0pt;">
        <tr><td colspan="2" height="118" style="{td}">{img('identite.png',303,118,label)}</td></tr>
        <tr>
          <td width="130" height="30" style="{td}"><a href="tel:{e(config['phone_href'], quote=True)}" aria-label="Appeler {e(config['phone_display'], quote=True)}" style="display:block;border:0;text-decoration:none;color:#ffffff;">{img('telephone.png',130,30,config['phone_display'])}</a></td>
          <td width="173" height="30" style="{td}">{img('portrait-bas.png',173,30)}</td>
        </tr>
      </table>
    </td>
    <td width="147" height="148" bgcolor="#ffffff" style="{td}width:147px;height:148px;">{img('impact-makers-3-lignes.gif',147,148,'WE ARE IMPACT MAKERS')}</td>
  </tr>
</table>'''


def document(table, title):
    return f'<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title></head><body style="margin:0;padding:0;background:#ffffff;">\n{table}\n</body></html>\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', nargs='?', default='EMMA L')
    args = parser.parse_args()
    folder = (ROOT / args.folder).resolve()
    config = json.loads((folder / 'signature.json').read_text())
    reference = Image.open(folder / config['reference']).convert('RGB')
    if reference.size == (1924, 634):
        reference = reference.crop((0, 1, 1924, 632)).resize((1924, 632), Image.Resampling.LANCZOS)
    assets = folder / 'assets'
    assets.mkdir(exist_ok=True)
    left = make_left(folder, config, reference).resize((606, 296), Image.Resampling.LANCZOS)
    for name, box in [('identite.png', (0, 0, 606, 236)),
                      ('telephone.png', (0, 236, 260, 296)),
                      ('portrait-bas.png', (260, 236, 606, 296))]:
        left.crop(box).save(assets / name, optimize=True)
    first, durations = make_animation(reference, assets / 'impact-makers-3-lignes.gif')
    title = f"Signature — {config['first_name']} {config['last_name']}"
    table = email_table(config, config['asset_base_url'])
    (folder / 'signature.html').write_text(document(table, title))
    (folder / 'signature-fragment.html').write_text(table + '\n')
    (folder / 'apercu-local.html').write_text(document(email_table(config, 'assets/'), title))
    preview = Image.new('RGB', (900, 296), 'white')
    preview.paste(left, (0, 0))
    preview.paste(first, (606, 0))
    preview.save(folder / 'apercu.png', optimize=True)
    print(f'{folder.name}: 450 × 148 px; {len(durations)} images source; boucle {sum(durations)} ms.')


if __name__ == '__main__':
    main()
