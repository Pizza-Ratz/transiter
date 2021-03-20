package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
)

const baseURL = "https://demo.transiter.dev"

func main() {
	rand.Seed(303)

	var response RootResponse
	_ = get(baseURL, &response)
	fmt.Println("Received system response, going to list systems")
	var listSystemsResponse []ListSystemsResponse
	_ = get(response.Systems.Href, &listSystemsResponse)
	fmt.Println("Received list systems response, choosing system")
	systemIndex := rand.Intn(len(listSystemsResponse))
	fmt.Println("Chose", listSystemsResponse[systemIndex].Name, ", now looking at the system")
	var systemResponse SystemResponse
	_ = get(listSystemsResponse[systemIndex].Href, &systemResponse)
	fmt.Println("Received system response, listing routes")
	var listRoutesResponse []ListRoutesResponse
	_ = get(systemResponse.Routes.Href, &listRoutesResponse)
	fmt.Println("Received routes in system response, choosing route")
	routeIndex := rand.Intn(len(listRoutesResponse))
	fmt.Println("Chose", listRoutesResponse[routeIndex].Id, ", now looking at that route")
	var routeResponse RouteResponse
	panicIfErr(get(listRoutesResponse[routeIndex].Href, &routeResponse))
	fmt.Println("Received route response, choosing random stop")
	serviceMapIndex := rand.Intn(len(routeResponse.Service_maps))
	stopIndex := rand.Intn(len(routeResponse.Service_maps[serviceMapIndex].Stops))
	fmt.Println("Chose", routeResponse.Service_maps[serviceMapIndex].Stops[stopIndex].Name, "now looking at that stop")
	var stopResponse StopResponse
	_ = get(routeResponse.Service_maps[serviceMapIndex].Stops[stopIndex].Href, &stopResponse)

}

func panicIfErr(err error) {
	if err != nil {
		panic(err)
	}
}

func get(url string, v interface{}) error {
	response, err := http.Get(url)
	if err != nil {
		return err
	}
	content, err := ioutil.ReadAll(response.Body)
	if err != nil {
		_ = response.Body.Close()
		return err
	}
	if err := response.Body.Close(); err != nil {
		return err
	}
	return json.Unmarshal(content, v)
}

type RootResponse struct {
	Systems struct {
		Count int
		Href string
	}
}

type ListSystemsResponse struct {
	Id string
	Name string
	Href string
}

type SystemResponse struct {
	Routes struct {
		Count int
		Href string
	}
}

type ListRoutesResponse struct {
	Id string
	Href string
}

type RouteResponse struct {
	Service_maps []struct {
		Group_id string
		Stops []struct{
			Id string
			Name string
			Href string
		}
	}
}

type StopResponse struct {
	Id string
	Name string
	Stop_times []struct {
		Trip struct {
			Id string
			Href string
		}
	}
}