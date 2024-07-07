from .serializers import OrderSerializer, GetOrderSerializer
from .models import Order
from rest_framework import viewsets
from django.http import HttpResponse
from django.http import JsonResponse  
import pandas as pd  
from rest_framework import views
from rest_framework.response import Response
from .utils import get_forecast_data
from .serializers import ForecastSerializer
from manufacture.models import Manufacture, Drug
from hospital.models import Hospital
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import math
import json
from rest_framework import status
from datetime import timedelta, datetime
import folium
from rest_framework import generics
from django_filters import rest_framework as filters
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

# Function to collect data from Django models
def collect_data():
    orders = Order.objects.all().values()
    hospitals = Hospital.objects.all().values()
    manufacturing_sites = Manufacture.objects.all().values()
    orders_df = pd.DataFrame(orders)
    hospital_df = pd.DataFrame(hospitals)
    manufacture_df = pd.DataFrame(manufacturing_sites)
    return orders_df, hospital_df, manufacture_df

def filter_orders_by_week(orders_df, start_date):
    # Convert start_date to pandas datetime
    start_date = pd.to_datetime(start_date)
    end_date = start_date + timedelta(days=7)
    # Ensure delivery_date is in datetime format
    orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date'])
    return orders_df[(orders_df['delivery_date'] >= start_date) & (orders_df['delivery_date'] < end_date)]

def allocate_orders(request):
    # Collect data
    orders_df, hospital_df, manufacture_df = collect_data()

    # Specify the week start date (Monday)
    start_date = request.GET.get('start_date')
    
    # Filter orders for the specified week
    weekly_orders_df = filter_orders_by_week(orders_df, start_date)
    
    # Prepare data for linear programming model
    manufacturing_sites = {}
    for _, row in manufacture_df.iterrows():
        manufacturing_sites[row['site_id']] = {
            "location": (row['latitude'], row['longitude']),
            "production_capacity": row['production_capacity']
        }
    hospitals = {}
    for _, row in hospital_df.iterrows():
        hospitals[row['hospital_id']] = {
            "location": (row['hospital_latitude'], row['hospital_longitude']),
            "demand": weekly_orders_df[weekly_orders_df['hospital_id'] == row['hospital_id']]['quantity'].sum()
        }

    # Cost calculation (assuming cost per kilometer is $1)
    cost_per_km = 1

    # Calculate the cost matrix C_ij
    cost_matrix = {}
    for ms_id, ms_data in manufacturing_sites.items():
        cost_matrix[ms_id] = {}
        for h_id, h_data in hospitals.items():
            distance = haversine(ms_data["location"][0], ms_data["location"][1], h_data["location"][0], h_data["location"][1])
            cost_matrix[ms_id][h_id] = cost_per_km * distance

    # Define the linear programming problem
    prob = LpProblem("Drug_Allocation_Problem", LpMinimize)

    # Define the decision variables
    x = LpVariable.dicts("X", (manufacturing_sites.keys(), hospitals.keys()), lowBound=0, cat='Continuous')

    # Objective function: Minimize the total cost of shipping
    prob += lpSum([x[ms_id][h_id] * cost_matrix[ms_id][h_id] for ms_id in manufacturing_sites for h_id in hospitals]), "Total_Transportation_Cost"

    # Constraints
    # All demand must be fulfilled
    for h_id in hospitals:
        prob += lpSum([x[ms_id][h_id] for ms_id in manufacturing_sites]) == hospitals[h_id]["demand"], f"Demand_{h_id}"

    # Production capacity constraint
    for ms_id in manufacturing_sites:
        prob += lpSum([x[ms_id][h_id] for h_id in hospitals]) <= manufacturing_sites[ms_id]["production_capacity"], f"Capacity_{ms_id}"

    # Solve the problem
    prob.solve(PULP_CBC_CMD(msg=0))

    # Output the results in JSON format
    total_cost = prob.objective.value()
    
    # Collect allocations respecting production capacities
    allocations = {}
    for h_id in hospitals:
        for ms_id in manufacturing_sites:
            quantity = x[ms_id][h_id].varValue
            if quantity > 0:
                if ms_id not in allocations:
                    allocations[ms_id] = {}
                allocations[ms_id][h_id] = quantity

    # Final allocation adjustment to respect production capacities
    final_allocations = {}
    for ms_id in allocations:
        final_allocations[ms_id] = {}
        total_allocated = 0
        for h_id in sorted(allocations[ms_id], key=lambda h: cost_matrix[ms_id][h]):
            if total_allocated + allocations[ms_id][h_id] <= manufacturing_sites[ms_id]["production_capacity"]:
                final_allocations[ms_id][h_id] = allocations[ms_id][h_id]
                total_allocated += allocations[ms_id][h_id]
            else:
                remaining_capacity = manufacturing_sites[ms_id]["production_capacity"] - total_allocated
                if remaining_capacity > 0:
                    final_allocations[ms_id][h_id] = remaining_capacity
                    total_allocated += remaining_capacity
                break

    response_data = {
        "cost_matrix": cost_matrix,
        "total_cost": total_cost,
        "allocations": [
            {"manufacturing_site": ms, "hospital": h, "quantity": int(final_allocations[ms][h])}
            for ms in final_allocations for h in final_allocations[ms] if int(final_allocations[ms][h]) > 0
        ]
    }

    return JsonResponse(response_data)
in this orders allocating based on minimun cost, how to inform this allocated orders to manufacture site and hospitals to track order details, start date is providing by admin(midator b/w manufacture site and hospitals)
now how connect this loop 
these are manufacture and hospital models
class Manufacture(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    site_id = models.CharField(max_length=255, unique=True,  primary_key=True)
    name = models.CharField(max_length=255)
    production_capacity = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=255)
   
    

    def __str__(self):
        return self.name
class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    hospital_id = models.CharField(max_length=255, unique=True, primary_key=True)
    hospital_name = models.CharField(max_length=255)
    hospital_latitude = models.FloatField()
    hospital_longitude = models.FloatField()
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=255)

    def __str__(self):
        return self.hospital_name
