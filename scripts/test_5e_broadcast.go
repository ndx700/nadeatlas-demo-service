package main
import (
  "crypto/sha256"
  "fmt"
  "io"
  "net/http"
  "os"
  "path/filepath"
  "sync"
  "sync/atomic"
  "time"
  demoinfocs "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs"
  events "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/events"
  "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/msg"
)
const base="https://hk-demo.5eplaycdn.com/game_tv/g201-20260922154948491976189"
var client=&http.Client{Timeout:30*time.Second}

func exists(n int) bool {
  req,_:=http.NewRequest("GET",fmt.Sprintf("%s/%d/delta",base,n),nil)
  req.Header.Set("Range","bytes=0-0")
  r,e:=client.Do(req); if e!=nil{return false}; defer r.Body.Close()
  io.Copy(io.Discard,r.Body)
  return r.StatusCode==200 || r.StatusCode==206
}
func get(url,path string) error {
  var last error
  for a:=0;a<4;a++ {
    r,e:=client.Get(url); if e==nil && (r.StatusCode==200||r.StatusCode==206) {
      f,e2:=os.Create(path); if e2!=nil {r.Body.Close();return e2}
      _,e2=io.Copy(f,r.Body); f.Close(); r.Body.Close()
      if e2==nil{return nil}; last=e2
    } else { if e==nil {last=fmt.Errorf("http %d",r.StatusCode);r.Body.Close()} else {last=e} }
    time.Sleep(time.Duration(a+1)*time.Second)
  }
  return last
}
func main(){
  // Find last archived delta fragment.
  lo,hi:=1,1
  for hi<8192 && exists(hi){lo=hi;hi*=2}
  for lo+1<hi {m:=(lo+hi)/2;if exists(m){lo=m}else{hi=m}}
  maxFrag:=lo
  fmt.Println("MAX_FRAGMENT",maxFrag)

  dir:="/tmp/5e-frags"; os.MkdirAll(dir,0755)
  if err:=get(base+"/0/start",filepath.Join(dir,"000000.start"));err!=nil{panic(err)}
  jobs:=make(chan int,64); var wg sync.WaitGroup; var failed atomic.Int64; var done atomic.Int64
  for w:=0;w<16;w++ {wg.Add(1);go func(){defer wg.Done();for n:=range jobs{
    p:=filepath.Join(dir,fmt.Sprintf("%06d.delta",n))
    if err:=get(fmt.Sprintf("%s/%d/delta",base,n),p);err!=nil{fmt.Println("DOWNLOAD_FAIL",n,err);failed.Add(1)}
    d:=done.Add(1);if d%100==0{fmt.Println("DOWNLOADED",d,"OF",maxFrag)}
  }}()}
  for n:=1;n<=maxFrag;n++{jobs<-n};close(jobs);wg.Wait()
  if failed.Load()>0{panic(fmt.Sprintf("%d fragments failed",failed.Load()))}

  outPath:="/tmp/5e-full.cstv"; out,err:=os.Create(outPath);if err!=nil{panic(err)}
  appendFile:=func(p string){f,e:=os.Open(p);if e!=nil{panic(e)};_,e=io.Copy(out,f);f.Close();if e!=nil{panic(e)}}
  appendFile(filepath.Join(dir,"000000.start"))
  for n:=1;n<=maxFrag;n++{appendFile(filepath.Join(dir,fmt.Sprintf("%06d.delta",n)))}
  out.Close()
  st,_:=os.Stat(outPath);fmt.Println("ARCHIVE_BYTES",st.Size())
  sf,_:=os.Open(outPath);h:=sha256.New();io.Copy(h,sf);sf.Close();fmt.Printf("ARCHIVE_SHA256 %x\n",h.Sum(nil))

  in,err:=os.Open(outPath);if err!=nil{panic(err)};defer in.Close()
  cfg:=demoinfocs.DefaultParserConfig;cfg.Format=demoinfocs.DemoFormatCSTVBroadcast
  p:=demoinfocs.NewParserWithConfig(in,cfg);defer p.Close()
  kills,rounds:=0,0;mapName:=""
  p.RegisterNetMessageHandler(func(m *msg.CDemoFileHeader){mapName=m.GetMapName();fmt.Println("HEADER_MAP",mapName)})
  p.RegisterEventHandler(func(e events.Kill){kills++})
  p.RegisterEventHandler(func(e events.RoundEnd){rounds++;if rounds%5==0{fmt.Println("ROUND_PROGRESS",rounds,"KILLS",kills)}})
  err=p.ParseToEnd()
  fmt.Println("PARSE_END",err)
  fmt.Println("FINAL_MAP",mapName,"KILLS",kills,"ROUNDS",rounds)
  if err!=nil || rounds<10 || kills<50 {os.Exit(2)}
}
