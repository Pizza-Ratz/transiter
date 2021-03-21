package main

import (
	"context"
	"fmt"
	"github.com/jamespfennell/transiter/tests/performance/client"
	"github.com/jamespfennell/transiter/tests/performance/stats"
	"math/rand"
	"sync"
	"time"
)

const baseURL = "https://demo.transiter.dev"

func main() {
	runWorkers()
	fmt.Println("-----STOPS-----")
	stats.StopStats.Print()
	fmt.Println("-----ROUTES-----")
	stats.RouteStats.Print()
	fmt.Println("-----TRIPS-----")
	stats.TripStats.Print()
}

func randDuration(lower, upper time.Duration) time.Duration {
	return lower + time.Duration(float64(upper-lower)*rand.Float64())
}

func runWorkers() {
	maxWorkers := 70
	minSpawnDelay := 50 * time.Millisecond
	maxSpawnDelay := 50 * time.Millisecond
	minActionPause := 500 * time.Millisecond
	maxActionPause := 1000 * time.Millisecond

	semaphore := NewSemaphore(maxWorkers)
	ctx, cancelFunc := context.WithDeadline(context.Background(), time.Now().Add(10*time.Second))
	defer cancelFunc()
	t := time.NewTicker(time.Second)
	defer t.Stop()
	rand.Seed(303)
	for {
		select {
		case <-semaphore.Acquire():
			time.Sleep(randDuration(minSpawnDelay, maxSpawnDelay))
			go func() {
				var state client.State
				var err error
				state = client.NewStartState(baseURL)
				for {
					state, err = state.Transition()
					if err != nil {
						fmt.Println("Error:", err)
					}
					if _, ok := state.(client.EndState); ok {
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
