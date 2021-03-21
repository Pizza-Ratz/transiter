package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"sync"
	"time"
)

const baseURL = "https://demo.transiter.dev"

type Stats struct {
	m     sync.Mutex
	data  map[string][]time.Duration
	nErrs int
}

func (stats *Stats) Add(id string, d time.Duration) {
	stats.m.Lock()
	defer stats.m.Unlock()
	stats.data[id] = append(stats.data[id], d)
}

func (stats *Stats) AddErr() {
	stats.m.Lock()
	defer stats.m.Unlock()
	stats.nErrs++
}

var stopStats Stats

func main() {
	stopStats = Stats{
		data: map[string][]time.Duration{},
	}
	runWorkers()
	for id, ds := range stopStats.data {
		fmt.Println(id, ds)
	}
}

func randDuration(lower, upper time.Duration) time.Duration {
	return lower + time.Duration(float64(upper-lower)*rand.Float64())
}

func runWorkers() {
	maxWorkers := 50
	minSpawnDelay := 50 * time.Millisecond
	maxSpawnDelay := 50 * time.Millisecond
	minActionPause := 500 * time.Millisecond
	maxActionPause := 500 * time.Millisecond

	semaphore := NewSemaphore(maxWorkers)
	ctx, cancelFunc := context.WithDeadline(context.Background(), time.Now().Add(50*time.Second))
	defer cancelFunc()
	t := time.NewTicker(time.Second)
	defer t.Stop()
	rand.Seed(303)
	for {
		select {
		case <-semaphore.Acquire():
			time.Sleep(randDuration(minSpawnDelay, maxSpawnDelay))
			go func() {
				var state State
				var err error
				state = StartState{baseUrl: baseURL}
				for {
					state, err = state.Transition()
					if err != nil {
						fmt.Println("Error:", err)
					}
					if _, ok := state.(EndState); ok {
						break
					}
					time.Sleep(randDuration(minActionPause, maxActionPause))
				}
				semaphore.Release()
			}()
		case <-t.C:
			fmt.Printf("Num workers: %d\n", semaphore.NumInUse())
		case <-ctx.Done():
			return
		}
	}
}

func NewSemaphore(size int) *Semaphore {
	s := Semaphore{
		c1:    make(chan struct{}),
		c2:    make(chan struct{}, size-1),
		nUsed: 0,
	}
	for i := 0; i < size-1; i++ {
		s.c2 <- struct{}{}
	}
	go func() {
		for {
			s.c1 <- struct{}{}
			s.m.Lock()
			s.nUsed++
			s.m.Unlock()
			<-s.c2
		}
	}()
	return &s
}

type Semaphore struct {
	c1    chan struct{}
	c2    chan struct{}
	m     sync.Mutex
	nUsed int
}

func (s *Semaphore) Acquire() <-chan struct{} {
	return s.c1
}

func (s *Semaphore) Release() {
	s.m.Lock()
	s.nUsed--
	s.m.Unlock()
	s.c2 <- struct{}{}
}

func (s *Semaphore) NumInUse() int {
	s.m.Lock()
	defer s.m.Unlock()
	return s.nUsed
}

type State interface {
	Transition() (State, error)
}

type StartState struct {
	baseUrl string
}

func (state StartState) Transition() (State, error) {
	var response RootResponse
	if _, err := get(state.baseUrl, &response); err != nil {
		return state, err
	}
	var listSystemsResponse []ListSystemsResponse
	if _, err := get(response.Systems.Href, &listSystemsResponse); err != nil {
		return state, err
	}
	systemIndex := rand.Intn(len(listSystemsResponse))
	var systemState SystemState
	if _, err := get(listSystemsResponse[systemIndex].Href, &systemState.systemResponse); err != nil {
		return state, err
	}
	return systemState, nil
}

type SystemState struct {
	systemResponse SystemResponse
}

func (state SystemState) Transition() (State, error) {
	var listRoutesResponse []ListRoutesResponse
	if _, err := get(state.systemResponse.Routes.Href, &listRoutesResponse); err != nil {
		return state, err
	}
	routeIndex := rand.Intn(len(listRoutesResponse))
	routeState, err := NewRouteState(listRoutesResponse[routeIndex].Href)
	if err != nil {
		return state, err
	}
	return routeState, nil
}

func NewRouteState(href string) (RouteState, error) {
	var routeState RouteState
	_, err := get(href, &routeState.routeResponse)
	return routeState, err
}

type RouteState struct {
	routeResponse RouteResponse
}

func (state RouteState) Transition() (State, error) {
	serviceMapIndex := state.selectServiceMap()
	if serviceMapIndex < 0 {
		return EndState{}, nil
	}
	stopIndex := rand.Intn(len(state.routeResponse.Service_maps[serviceMapIndex].Stops))
	stopState, err := NewStopState(state.routeResponse.Service_maps[serviceMapIndex].Stops[stopIndex].Href)
	if err != nil {
		return state, err
	}
	return stopState, nil
}

func (state RouteState) selectServiceMap() int {
	randIndex := rand.Intn(len(state.routeResponse.Service_maps))
	if len(state.routeResponse.Service_maps[randIndex].Stops) > 0 {
		return randIndex
	}
	for i := 0; i < len(state.routeResponse.Service_maps); i++ {
		if len(state.routeResponse.Service_maps[i].Stops) > 0 {
			return i
		}
	}
	return -1
}

func NewStopState(href string) (StopState, error) {
	var stopState StopState
	d, err := get(href, &stopState.stopResponse)
	if err != nil {
		stopStats.AddErr()
	} else {
		stopStats.Add(stopState.stopResponse.Id, d)
	}
	return stopState, err
}

type StopState struct {
	stopResponse StopResponse
}

func (state StopState) Transition() (State, error) {
	return EndState{}, nil
}

type EndState struct{}

func (state EndState) Transition() (State, error) {
	panic("Can't transition out of the end state")
}

func get(url string, v interface{}) (time.Duration, error) {
	start := time.Now()
	response, err := http.Get(url)
	d := time.Now().Sub(start)
	if err != nil {
		return d, err
	}
	content, err := ioutil.ReadAll(response.Body)
	if err != nil {
		_ = response.Body.Close()
		return d, err
	}
	if err := response.Body.Close(); err != nil {
		return d, err
	}
	return d, json.Unmarshal(content, v)
}

type RootResponse struct {
	Systems struct {
		Count int
		Href  string
	}
}

type ListSystemsResponse struct {
	Id   string
	Name string
	Href string
}

type SystemResponse struct {
	Routes struct {
		Count int
		Href  string
	}
}

type ListRoutesResponse struct {
	Id   string
	Href string
}

type RouteResponse struct {
	Service_maps []struct {
		Group_id string
		Stops    []struct {
			Id   string
			Name string
			Href string
		}
	}
}

type StopResponse struct {
	Id         string
	Name       string
	Stop_times []struct {
		Trip struct {
			Id   string
			Href string
		}
	}
}
