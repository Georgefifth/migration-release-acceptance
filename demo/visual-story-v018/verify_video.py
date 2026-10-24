"""Decode the delivered video and compare actual card frames with designed PNGs."""
from pathlib import Path
import subprocess,json,re,hashlib,sys,math
from array import array
from PIL import Image,ImageChops,ImageStat
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/demo-visuals-v018'
VOICED='--voiced' in sys.argv
MODE='voiced-video' if VOICED else 'verified-video-safe'
VIDEO=OUT/MODE/'demo.mp4'
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
def frame(t,dest):
 subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(VIDEO),'-frames:v','1','-y',str(dest)],check=True)
metadata=probe(VIDEO);duration=float(metadata['format']['duration']);stream=next(s for s in metadata['streams'] if s['codec_type']=='video')
assert (stream['width'],stream['height'],stream['codec_name'])==(1920,1080,'h264')
scenes=json.loads((OUT/MODE/'scenes.used.json').read_text());manifest=json.loads((OUT/MODE/'timestamps.json').read_text())
assert len(scenes)==len(manifest)==15 and not any(m.get('error') for m in manifest)
frames=OUT/'.build'/('voiced-video-frames' if VOICED else 'video-frames');frames.mkdir(exist_ok=True);rows=[];offset=0
for i,s in enumerate(scenes):
 segment=OUT/MODE/'segs'/f'seg-{i:02}.mp4';length=float(probe(segment)['format']['duration'])
 midpoint=offset+length/2;dest=frames/f'{i:02}-{s["name"]}.png';frame(midpoint,dest)
 row=dict(scene=i,name=s['name'],start=round(offset,3),duration=length,midpoint=round(midpoint,3),frame=str(dest.relative_to(ROOT)))
 if s.get('card'):
  actual=Image.open(dest).convert('RGB').crop((0,0,1920,900));expected=Image.open(s['card']['image']).convert('RGB').crop((0,0,1920,900))
  error=sum(ImageStat.Stat(ImageChops.difference(actual,expected)).mean)/3
  row['card_top900_mean_abs_pixel_error']=round(error,3);assert error<6,(s['name'],error)
 else:
  frame(offset+1.3,frames/f'{i:02}-focus.png')
 if VOICED:
  voice_file=OUT/MODE/'segs'/f'vo-{i:02}.mp3'
  voice_duration=float(probe(voice_file)['format']['duration'])
  assert voice_duration>1 and voice_duration+0.4<=length+0.1,(s['name'],voice_duration,length)
  voice_pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(voice_file),'-ac','1','-ar','16000','-f','s16le','-'])
  samples=array('h',voice_pcm);peak=max(abs(x) for x in samples)
  rms=math.sqrt(sum(x*x for x in samples)/len(samples))/32768
  assert peak>500 and rms>0.005,(s['name'],peak,rms)
  row.update(voice_seconds=voice_duration,voice_sha256=hashlib.sha256(voice_file.read_bytes()).hexdigest(),voice_peak_dbfs=round(20*math.log10(peak/32768),2),voice_rms_dbfs=round(20*math.log10(rms),2),requested_text_sha256=hashlib.sha256(s['vo'].encode()).hexdigest())
 rows.append(row);offset+=length
assert abs(offset-duration)<0.6,(offset,duration)
result=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-f','null','-'],capture_output=True,text=True)
assert result.returncode==0 and not result.stderr,result.stderr
# Silent audio is intentional, not a broken or unverified narration claim.
audio=subprocess.run(['ffmpeg','-hide_banner','-i',str(VIDEO),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True)
assert audio.returncode==0,audio.stderr[-1000:]
pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(VIDEO),'-vn','-acodec','pcm_s16le','-f','s16le','-'])
if VOICED:
 assert pcm and any(pcm), 'Final audio must contain narration'
else:
 assert pcm and not any(pcm), 'Decoded audio must contain zero-valued PCM samples'
ass=(OUT/MODE/'captions.ass').read_text();captions=[line for line in ass.splitlines() if line.startswith('Dialogue:')]
assert len(captions)>=15
assert all(len(line.split(',',9)[-1])<=90 for line in captions)
receipt=dict(video=str(VIDEO.relative_to(ROOT)),sha256=hashlib.sha256(VIDEO.read_bytes()).hexdigest(),duration_seconds=duration,canvas=[1920,1080],codec='h264',scene_count=15,capture_errors=0,decode_errors=0,caption_cues=len(captions),spoken_audio=VOICED,silent_audio_verified=not VOICED,scenes=rows,boundary='Machine checks plus extracted frames. Actual UI/transition readability requires visual review, recorded separately.')
(OUT/('voiced-video-verification.json' if VOICED else 'video-verification.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='scenes'},indent=2))
