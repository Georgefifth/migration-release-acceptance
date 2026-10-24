"""Decode the delivered video and compare actual card frames with designed PNGs."""
from pathlib import Path
import subprocess,json,re,hashlib
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/demo-visuals-v018';VIDEO=OUT/'verified-video-safe/demo.mp4'
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def frame(t,dest):
 subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-y',str(dest)],check=True)
metadata=probe(VIDEO);duration=float(metadata['format']['duration']);stream=next(s for s in metadata['streams'] if s['codec_type']=='video')
assert (stream['width'],stream['height'],stream['codec_name'])==(1920,1080,'h264')
scenes=json.loads((OUT/'verified-video-safe/scenes.used.json').read_text());manifest=json.loads((OUT/'verified-video-safe/timestamps.json').read_text())
assert len(scenes)==len(manifest)==15 and not any(m.get('error') for m in manifest)
frames=OUT/'.build/video-frames';frames.mkdir(exist_ok=True);rows=[];offset=0
for i,s in enumerate(scenes):
 segment=OUT/'verified-video-safe/segs'/f'seg-{i:02}.mp4';length=float(probe(segment)['format']['duration'])
 midpoint=offset+length/2;dest=frames/f'{i:02}-{s["name"]}.png';frame(midpoint,dest)
 row=dict(scene=i,name=s['name'],start=round(offset,3),duration=length,midpoint=round(midpoint,3),frame=str(dest.relative_to(ROOT)))
 if s.get('card'):
  actual=Image.open(dest).convert('RGB').crop((0,0,1920,900));expected=Image.open(s['card']['image']).convert('RGB').crop((0,0,1920,900))
  error=sum(ImageStat.Stat(ImageChops.difference(actual,expected)).mean)/3
  row['card_top900_mean_abs_pixel_error']=round(error,3);assert error<6,(s['name'],error)
 else:
  frame(offset+1.3,frames/f'{i:02}-focus.png')
 rows.append(row);offset+=length
assert abs(offset-duration)<0.6,(offset,duration)
result=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True,text=True)
assert result.returncode==0 and not result.stderr,result.stderr
# Silent audio is intentional, not a broken or unverified narration claim.
audio=subprocess.run(['ffmpeg','-hide_banner','-i',str(VIDEO),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True)
assert audio.returncode==0,audio.stderr[-1000:]
pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(VIDEO),'-vn','-acodec','pcm_s16le','-f','s16le','-'])
assert pcm and not any(pcm), 'Decoded audio must contain zero-valued PCM samples'
ass=(OUT/'verified-video-safe/captions.ass').read_text();captions=[line for line in ass.splitlines() if line.startswith('Dialogue:')]
assert len(captions)>=15
assert all(len(line.split(',',9)[-1])<=90 for line in captions)
receipt=dict(video=str(VIDEO.relative_to(ROOT)),sha256=hashlib.sha256(VIDEO.read_bytes()).hexdigest(),duration_seconds=duration,canvas=[1920,1080],codec='h264',scene_count=15,capture_errors=0,decode_errors=0,caption_cues=len(captions),spoken_audio=False,silent_audio_verified=True,scenes=rows,boundary='Machine checks plus extracted frames. Actual UI/transition readability requires visual review, recorded separately.')
(OUT/'video-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='scenes'},indent=2))
