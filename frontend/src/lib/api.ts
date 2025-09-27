const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://standing-fish-574.convex.site";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: Response
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(
      `API Error: ${response.status} ${response.statusText}`,
      response.status,
      response
    );
  }

  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return await response.json();
  }

  // If not JSON, return empty object
  return {} as T;
}

export async function apiGet<T>(endpoint: string): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    return await handleResponse<T>(response);
  } catch (error) {
    console.error(`API GET Error for ${endpoint}:`, error);
    if (error instanceof ApiError) {
      console.error(`Status: ${error.status}`);
    }
    // Return empty array/object instead of throwing
    return (Array.isArray({}) ? [] : {}) as T;
  }
}

export async function apiPost<T, D = unknown>(
  endpoint: string,
  data: D
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    return await handleResponse<T>(response);
  } catch (error) {
    console.error(`API POST Error for ${endpoint}:`, error);
    console.error(`Request data:`, data);
    if (error instanceof ApiError) {
      console.error(`Status: ${error.status}`);
    }
    // Return empty object instead of throwing
    return {} as T;
  }
}

// Utility function to build query parameters
export function buildQueryParams(
  params: Record<string, string | undefined>
): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.append(key, value);
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}
