#!/usr/bin/env python3
"""Create a real layered .aseprite file using Aseprite's published file format.

This validates the serialized format, NOT the Aseprite editor or Lua runtime.
"""
import argparse
import struct
import zlib
from pathlib import Path
from PIL import Image

LAYERS = [
    ('REFERENCE - Crystal', 'crystal_reference_56.png', False),
    ('REFERENCE - FireRed fitted', 'firered_placed_56.png', False),
    ('00 - Luminance baseline', 'preview_00_luma.png', False),
    ('01 - Region-aware colours', 'preview_01_regions.png', False),
    ('02 - Interior shade cleanup', 'preview_02_cleanup.png', True),
]

def chunk(kind, data):
    return struct.pack('<IH',len(data)+6,kind)+data

def build(root):
    chunks=[]
    imgs=[]
    for name,filename,visible in LAYERS:
        with Image.open(root/filename) as img:
            im=img.convert('RGBA')
        if im.size!=(56,56):raise ValueError(f'{filename}: invalid dimensions {im.size}')
        imgs.append(im)
        name_data=name.encode('utf8')
        flags=2+(1 if visible else 0)
        layer=struct.pack('<HHHHHHB3s',flags,0,0,0,0,0,255,b'\0'*3)
        chunks.append(chunk(0x2004,layer+struct.pack('<H',len(name_data))+name_data))
    for i,img in enumerate(imgs):
        head=struct.pack('<HhhBHh5sHH',i,0,0,255,2,0,b'\0'*5,56,56)
        chunks.append(chunk(0x2005,head+zlib.compress(img.tobytes(),9)))
    body=b''.join(chunks)
    frame=struct.pack('<IHHH2sI',16+len(body),0xF1FA,len(chunks),100,b'\0'*2,len(chunks))+body
    header=bytearray(128)
    struct.pack_into('<IHHHHHIHII',header,0,128+len(frame),0xA5E0,1,56,56,32,1,100,0,0)
    struct.pack_into('<B3sHBBhhHH',header,28,0,b'\0'*3,0,1,1,0,0,16,16)
    out=root/'youngster_candidates.aseprite'
    out.write_bytes(bytes(header)+frame)
    validate(out,imgs)
    print(f'Created editable source: {out} ({len(imgs)} layers, 56x56)')

def validate(path,imgs):
    raw=path.read_bytes()
    size,magic,frames,w,h,depth=struct.unpack_from('<IHHHHH',raw,0)
    assert (size,magic,frames,w,h,depth)==(len(raw),0xA5E0,1,56,56,32)
    fsize,fmagic,n=struct.unpack_from('<IHH',raw,128)
    assert (fsize,fmagic,n)==(len(raw)-128,0xF1FA,2*len(imgs))
    offset=144
    layers=[]
    cels={}
    for _ in range(n):
        length,kind=struct.unpack_from('<IH',raw,offset)
        assert length>=6 and offset+length<=len(raw)
        data=raw[offset+6:offset+length]
        if kind==0x2004:
            flags,layer_type=struct.unpack_from('<HH',data)
            assert layer_type==0
            nlen=struct.unpack_from('<H',data,16)[0]
            layers.append(data[18:18+nlen].decode('utf8'))
            assert bool(flags&1)==LAYERS[len(layers)-1][2]
        elif kind==0x2005:
            idx,x,y,opacity,ctype=struct.unpack_from('<HhhBH',data)
            cw,ch=struct.unpack_from('<HH',data,16)
            assert (x,y,opacity,ctype,cw,ch)==(0,0,255,2,56,56)
            cels[idx]=zlib.decompress(data[20:])
        offset+=length
    assert offset==len(raw)
    assert layers==[name for name,_,_ in LAYERS]
    assert len(cels)==len(imgs)
    for i,img in enumerate(imgs):assert cels[i]==img.tobytes()
    print('Validated all Aseprite layer chunks, compressed cels, and exact PNG pixel parity.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dir',type=Path,default=Path('build/aseprite-youngster'))
    opts=p.parse_args()
    build(opts.dir)

if __name__=='__main__':
    main()
