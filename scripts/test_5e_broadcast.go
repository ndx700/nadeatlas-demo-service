package main
import (
  "fmt"
  "time"
  demoinfocs "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs"
  events "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/events"
  "github.com/markus-wa/demoinfocs-golang/v5/pkg/demoinfocs/msg"
)
func main(){
  u:="https://hk-demo.5eplaycdn.com/game_tv/g201-20260922154948491976189"
  cfg:=demoinfocs.DefaultParserConfig
  cfg.CSTVTimeout=12*time.Second
  p,err:=demoinfocs.NewCSTVBroadcastParserWithConfig(u,cfg)
  if err!=nil { panic(err) }
  defer p.Close()
  kills,rounds:=0,0
  p.RegisterNetMessageHandler(func(m *msg.CDemoFileHeader){fmt.Println("HEADER_MAP",m.GetMapName())})
  p.RegisterEventHandler(func(e events.Kill){kills++})
  p.RegisterEventHandler(func(e events.RoundEnd){rounds++})
  err=p.ParseToEnd()
  fmt.Println("PARSE_END",err)
  fmt.Println("KILLS",kills,"ROUNDS",rounds)
}
