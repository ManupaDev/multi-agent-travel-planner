import { apiGet } from "@/lib/api";
import type {
  CitiesResponse,
  CountriesResponse,
  RoutesResponse,
  UsageStatsResponse,
} from "@/lib/types";

export const referenceApi = {
  // Get all cities
  getCities: (): Promise<CitiesResponse> => {
    return apiGet<CitiesResponse>("/reference/cities");
  },

  // Get all countries
  getCountries: (): Promise<CountriesResponse> => {
    return apiGet<CountriesResponse>("/reference/countries");
  },

  // Get all routes
  getRoutes: (): Promise<RoutesResponse> => {
    return apiGet<RoutesResponse>("/reference/routes");
  },

  // Get usage statistics
  getUsageStats: (): Promise<UsageStatsResponse> => {
    return apiGet<UsageStatsResponse>("/admin/usage-stats");
  },
};

// Cache for reference data
let citiesCache: CitiesResponse | null = null;
let countriesCache: CountriesResponse | null = null;
let routesCache: RoutesResponse | null = null;

export const getCachedCities = async (): Promise<CitiesResponse> => {
  if (!citiesCache) {
    citiesCache = await referenceApi.getCities();
  }
  return citiesCache;
};

export const getCachedCountries = async (): Promise<CountriesResponse> => {
  if (!countriesCache) {
    countriesCache = await referenceApi.getCountries();
  }
  return countriesCache;
};

export const getCachedRoutes = async (): Promise<RoutesResponse> => {
  if (!routesCache) {
    routesCache = await referenceApi.getRoutes();
  }
  return routesCache;
};
