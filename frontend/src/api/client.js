const API_BASE_URL = ''; // Relative path because of proxy

export const checkHealth = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return await response.json();
    } catch (error) {
        console.error('Health check failed:', error);
        throw error;
    }
};

export const solvePDE = async (data) => {
    try {
        const response = await fetch(`${API_BASE_URL}/solve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Solver failed');
        }
        return await response.json();
    } catch (error) {
        console.error('Solver request failed:', error);
        throw error;
    }
};
