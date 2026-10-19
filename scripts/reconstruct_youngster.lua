-- Aseprite v1.3+; run after scripts/prepare_aseprite_youngster.py.
-- aseprite -b --script-param root=build/aseprite-youngster --script scripts/reconstruct_youngster.lua
-- This generates diagnostic candidates, NOT professional-quality art.
local dir = (app.params and app.params.root) or "build/aseprite-youngster"
local pc = app.pixelColor
local W,H=56,56
local grey={255,170,85,0}
local function file(n) return dir.."/"..n end
local source=assert(Image{fromFile=file("firered_placed_56.png")})
local masks=assert(Image{fromFile=file("regions_56.png")})
local native=assert(Image{fromFile=file("crystal_reference_56.png")})
for _,im in ipairs({source,masks,native}) do
  assert(im.width==W and im.height==H, "Expected 56x56 source, masks and reference")
end
assert(source.colorMode==ColorMode.RGB and masks.colorMode==ColorMode.RGB,
       "Source and masks must be RGB-mode RGBA PNGs")
local function region(x,y)
  local pixel=masks:getPixel(x,y)
  if pc.rgbaA(pixel)<128 then return 0 end
  return math.floor(pc.rgbaR(pixel)/20+0.5)
end
local function level(pixel,id,semantic)
  local r,g,b=pc.rgbaR(pixel),pc.rgbaG(pixel),pc.rgbaB(pixel)
  local lum=math.floor((299*r+587*g+114*b)/1000+0.5)
  local a,c,d=64,128,200
  if semantic then
    if id==1 or id==7 then a,c,d=76,148,210
    elseif id==2 or id==4 or id==5 or id==8 then a,c,d=70,135,195
    elseif id==6 then a,c,d=65,126,187
    else a,c,d=68,127,196 end
  end
  if lum<a then return 4 elseif lum<c then return 3
  elseif lum<d then return 2 else return 1 end
end
local function index_grid(semantic)
  local result,ids={},{}
  for y=0,H-1 do
    result[y+1],ids[y+1]={},{}
    for x=0,W-1 do
      local color=source:getPixel(x,y)
      local id=region(x,y)
      ids[y+1][x+1]=id
      result[y+1][x+1]=(id>0 and pc.rgbaA(color)>=128) and level(color,id,semantic) or 1
    end
  end
  return result,ids
end
local function as_image(levels)
  local im=Image(W,H,ColorMode.RGB)
  for y=0,H-1 do
    for x=0,W-1 do
      local v=grey[levels[y+1][x+1]]
      im:drawPixel(x,y,pc.rgba(v,v,v,255))
    end
  end
  return im
end
local basic,ids=index_grid(false)
local colored=index_grid(true)
local cleaned={}
for y=1,H do
  cleaned[y]={}
  for x=1,W do cleaned[y][x]=colored[y][x] end
end
local count=0
-- Modify only homogeneous interior shade pixels of broad clothing regions;
-- never touch face, ball, outlines, background or the outside silhouette.
for y=2,H-1 do
  for x=2,W-1 do
    local id=ids[y][x]
    if id==6 or id==7 or id==8 then
      local neighbors={{x-1,y},{x+1,y},{x,y-1},{x,y+1}}
      local frequency,valid={},true
      for _,xy in ipairs(neighbors) do
        local nx,ny=xy[1],xy[2]
        if ids[ny][nx]~=id then valid=false break end
        local v=colored[ny][nx]
        frequency[v]=(frequency[v] or 0)+1
      end
      if valid and colored[y][x]~=4 then
        for v,n in pairs(frequency) do
          if n>=3 and v~=4 and colored[y][x]~=v then
            cleaned[y][x]=v;count=count+1
          end
        end
      end
    end
  end
end
local a,b,c=as_image(basic),as_image(colored),as_image(cleaned)
a:saveAs(file("candidate_00_luma.png"))
b:saveAs(file("candidate_01_regions.png"))
c:saveAs(file("candidate_02_cleanup.png"))
local sprite=Sprite(W,H,ColorMode.RGB)
local function add_layer(name,im,show,existing)
  local layer=existing or sprite:newLayer()
  layer.name=name
  local cel=layer:cel(1)
  if cel then cel.image=Image(im)
  else sprite:newCel(layer,1,Image(im),Point(0,0)) end
  layer.isVisible=show
end
add_layer("REFERENCE - Crystal",native,false,sprite.layers[1])
add_layer("REFERENCE - FireRed fitted",source,false)
add_layer("00 - Luminance baseline",a,false)
add_layer("01 - Region-aware colours",b,false)
add_layer("02 - Safe interior cleanup",c,true)
sprite:saveAs(file("youngster_candidates.aseprite"))
print("Wrote PNG candidates and layered Aseprite source. Interior changes: "..tostring(count))
