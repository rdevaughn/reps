from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader

import requests
from operator import itemgetter

import sunlight

from .forms import ZipForm
from .forms import AddressForm

def index(request):
    # post requests come from the zip or address forms
    if request.method == 'POST':
        try:
            if request.POST["street"]:
                form = AddressForm(request.POST)
                if form.is_valid():
                    # get lat/lng from address
                    location = geoSearch(form.cleaned_data["zip"], form.cleaned_data["street"])
                    return HttpResponseRedirect("/demo/?zip=" + location["zip"] + "&lat=" + str(location["lat"]) + "&lng=" + str(location["lng"]))
        except:
            pass
        form = ZipForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect("/demo/?zip=" + form.cleaned_data["zip"])
    else:
        zip = request.GET.get("zip","")
        lat = request.GET.get("lat","")
        lng = request.GET.get("lng","")
        form = ZipForm()
        context = {"form": form}
        if lat != "" and lng != "":
            fed_reps = fedRepsByGeo(lat,lng)
            state_reps = stateRepsByGeo(lat,lng)
            execs = allExecs(zip)
            context = {"zip"  : zip,
                       "fed_reps" : fed_reps,
                       "fed_execs": execs[0],
                       "state_execs": execs[1],
                       "form": form,
                       "lat": lat,
                       "lng": lng,
                       "state_reps": state_reps,
                       "reloaded" : True }
        elif zip != "":
            fed_reps = fedRepsByZip(zip)
            execs = allExecs(zip)
            location = geoSearch(zip)
            context = {"zip"  : zip,
                       "fed_reps" : fed_reps,
                       "fed_execs": execs[0],
                       "state_execs": execs[1],
                       "form": form,
                       "lat": location["lat"],
                       "lng": location["lng"]}

        template = loader.get_template("demo/index.html")
        return HttpResponse(template.render(context, request))

def geoSearch(zip, street=""):
    if street == "":
        url = "http://maps.googleapis.com/maps/api/geocode/json?address=" + zip
    else:
        url = "http://maps.googleapis.com/maps/api/geocode/json?address=" + street + " " + zip
    response = requests.get(url)
    json = response.json()
    location = json["results"][0]["geometry"]["location"]
    location["zip"] = zip
    if street != "":
        for comp in json["results"][0]["address_components"]:
            if comp["types"][0] == "postal_code":
                location["zip"] = str(comp["long_name"])
    return location

def fedRepsByZip(zip):
    response = sunlight.congress.locate_legislators_by_zip(zip)
    reps = []
    for legislator in response:
        rep = {}
        rep["first_name"] = str(legislator["first_name"])
        rep["last_name"] = str(legislator["last_name"])
        rep["party"] = str(legislator["party"]).upper()
        rep["title"] = "Senator" if legislator["chamber"] == "senate" else "Representative"
        rep["phone"] = str(legislator["phone"])
        rep["twitter"] = str(legislator["twitter_id"])
        try:
            rep["votesmart"] = str(legislator["votesmart_id"])
        except:
            pass
        rep["facebook"] = str(legislator["facebook_id"])
        try:
            rep["youtube"] = str(legislator["youtube_id"])
        except:
            pass
        rep["contact"] = str(legislator["contact_form"])
        rep["office"] = str(legislator["office"])
        reps.append(rep)
    reps = sorted(reps, key=itemgetter('title'), reverse=True)
    return reps

def fedRepsByGeo(lat, lng):
    response = sunlight.congress.locate_legislators_by_lat_lon(lat, lng)
    reps = []
    for legislator in response:
        rep = {}
        rep["first_name"] = str(legislator["first_name"])
        rep["last_name"] = str(legislator["last_name"])
        rep["party"] = str(legislator["party"]).upper()
        rep["title"] = "Senator" if legislator["chamber"] == "senate" else "Representative"
        rep["phone"] = str(legislator["phone"])
        rep["twitter"] = str(legislator["twitter_id"])
        try:
            rep["votesmart"] = str(legislator["votesmart_id"])
        except:
            pass
        rep["facebook"] = str(legislator["facebook_id"])
        try:
            rep["youtube"] = str(legislator["youtube_id"])
        except:
            pass
        rep["contact"] = str(legislator["contact_form"])
        rep["office"] = str(legislator["office"])
        reps.append(rep)
    reps = sorted(reps, key=itemgetter('title'), reverse=True)
    return reps

def stateRepsByGeo(lat, lng):
    try:
        response = sunlight.openstates.legislator_geo_search(lat,lng)
        reps = []
        for legislator in response:
            rep = {}
            rep["first_name"] = str(legislator["first_name"])
            rep["last_name"] = str(legislator["last_name"].encode('utf-8'))
            rep["party"] = str(legislator["party"][0]).upper()
            rep["chamber"] = str(legislator["chamber"]).title()
            rep["phone"] = str(legislator["offices"][0]["phone"])
            rep["email"] = str(legislator["email"])
            rep["office"] = str(legislator["offices"][0]["address"]).replace("\n","<br />")
            try:
                rep["votesmart"] = str(legislator["votesmart_id"])
            except:
                pass
            reps.append(rep)
        reps = sorted(reps, key=itemgetter('chamber'), reverse=True)
        return reps
    except:
        return ""

def allExecs(zip):
    url = "https://www.googleapis.com/civicinfo/v2/representatives?address=" + zip + "&key=AIzaSyB81jaFOXf7mxIPfMtOPJiuJ2geLFwialo"
    response = requests.get(url)
    json = response.json()

    allReps = []
    for index, office in enumerate(json["offices"]):
        for official in office["officialIndices"]:
            rep = {}
            rep["office"] = str(office["name"])
            rep["name"] = str(json["officials"][official]["name"])
            if office["divisionId"] == "ocd-division/country:us":
                rep["level"] = "Federal"
                rep["branch"] = "Executive"
            elif "ocd-division/country:us/state:" in office["divisionId"] and "United States" in office["name"]:
                rep["level"] = "Federal"
                rep["branch"] = "Legislative"
            else:
                rep["level"] = "State"
                rep["branch"] = "Executive"
            rep["party"] = str(json["officials"][official]["party"][0])
            try:
                rep["phone"] = str(json["officials"][official]["phones"][0])
            except:
                pass
            try:
                for channel in json["officials"][official]["channels"]:
                    if channel["type"] == "Twitter":
                        rep["twitter"] = str(channel["id"])
                    elif channel["type"] == "Facebook":
                        rep["facebook"] = str(channel["id"])
                    elif channel["type"] == "YouTube":
                        rep["youtube"] = str(channel["id"])
            except:
                pass
            try:
                rep["address"] = str(json["officials"][official]["address"][0]["line1"].title() + "<br />" + json["officials"][official]["address"][0]["line2"].title() + "<br />" + json["officials"][official]["address"][0]["city"].title() + ", " + json["officials"][official]["address"][0]["state"].upper() + " " + json["officials"][official]["address"][0]["zip"])
            except:
                try:
                    rep["address"] = str(json["officials"][official]["address"][0]["line1"].title() + "<br />" + json["officials"][official]["address"][0]["city"].title() + ", " + json["officials"][official]["address"][0]["state"].upper() + " " + json["officials"][official]["address"][0]["zip"])
                except:
                    pass

            allReps.append(rep)
    fed_execs = []
    state_execs = []
    for rep in allReps:
        if rep["branch"] != "Legislative":
            if rep["level"] == "Federal":
                fed_execs.append(rep)
            else:
                state_execs.append(rep)
    return (fed_execs, state_execs)
