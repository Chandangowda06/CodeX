import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams } from 'react-router-dom';
import TruckLoader from './loaders/TruckLoader';

interface Hospital {
    id: number;
    hospital_id: string;
    hospital_name: string;
    hospital_latitude: number;
    hospital_longitude: number;
    street_address: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
}

interface ManufacturingSite {
    site_id: string;
    name: string;
    latitude: number;
    longitude: number;
    street_address: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    production_capacity: number;
    production_schedule: string;
    expire_in: string;
}

const OptimizationComponent: React.FC = () => {
    const { siteId, hospitalId } = useParams<{ siteId: string; hospitalId: string }>();
    const [routeMapHtml, setRouteMapHtml] = useState<string>('');
    const [error, setError] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(true);
    const [hospital, setHospital] = useState<Hospital | null>(null);
    const [manufacturingSite, setManufacturingSite] = useState<ManufacturingSite | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                // Fetch route map
                const response = await axios.post('http://127.0.0.1:8000/transportation-api/optimize-route/', {
                    site_id: siteId,
                    hospital_id: hospitalId,
                });
                setRouteMapHtml(response.data.route_map_html);

                // Fetch hospital data
                const hospitalResponse = await axios.get<Hospital[]>(`http://127.0.0.1:8000/hospital-api/hospitals/?hospital_id=${hospitalId}`);
                setHospital(hospitalResponse.data[0]); // Assuming the response is an array, set the first item
                
                // Fetch manufacturing site data
                const siteResponse = await axios.get<ManufacturingSite[]>(`http://127.0.0.1:8000/manufacture-api/manufacture/?site_id=${siteId}`);
                setManufacturingSite(siteResponse.data[0]);

                setError('');
            } catch (err: any) {
                if (err.response) {
                    // The request was made and the server responded with a status code outside of the 2xx range
                    setError(`Error: ${err.response.status} - ${err.response.data.detail || err.response.statusText}`);
                } else if (err.request) {
                    // The request was made but no response was received
                    setError('Error: No response received from the server. Please try again later.');
                } else {
                    // Something happened in setting up the request that triggered an error
                    setError(`Error: ${err.message}`);
                }
                console.error('Error fetching data:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [siteId, hospitalId]);

    return (
        <>
            {loading ? (
                <div className="flex justify-center items-center">
                    <TruckLoader />
                </div>
            ) : error ? (
                <p className="text-red-500 text-center">{error}</p>
            ) : (
                <>
                    <div className="container mx-auto p-4">
                        {manufacturingSite && (
                            <div className="bg-white shadow-lg rounded-lg p-6 mb-4">
                                <h2 className="text-2xl font-bold mb-2 text-blue-600">Manufacturing Site Details</h2>
                                <p className="text-gray-700"><span className="font-semibold">Name:</span> {manufacturingSite.name}</p>
                                <p className="text-gray-700"><span className="font-semibold">Location:</span>{manufacturingSite.street_address} {manufacturingSite.city} {manufacturingSite.state} {manufacturingSite.country} - {manufacturingSite.postal_code}</p>
                            </div>
                        )}
                        {hospital && (
                            <div className="bg-white shadow-lg rounded-lg p-6 mb-4">
                                <h2 className="text-2xl font-bold mb-2 text-green-600">Hospital Details</h2>
                                <p className="text-gray-700"><span className="font-semibold">Name:</span> {hospital.hospital_name}</p>
                                <p className="text-gray-700"><span className="font-semibold">Address:</span> {hospital.street_address} {hospital.city} {hospital.state} {hospital.country} - {hospital.postal_code}</p>
                            </div>
                        )}
                        <div dangerouslySetInnerHTML={{ __html: routeMapHtml }} className="w-full h-full mt-4 border-t pt-4" />
                    </div>
                </>
            )}
        </>
    );
};

export default OptimizationComponent;
