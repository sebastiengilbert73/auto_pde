import { useState } from 'react';
import './PDEForm.css';

const PDEForm = ({ onSubmit, isLoading }) => {
    const [formData, setFormData] = useState({
        equation: 'uxx + uyy',
        ic: 'sin(x)*sin(y)',
        domain: {
            x_min: 0,
            x_max: 3.14159,
            y_min: 0,
            y_max: 3.14159,
            t_max: 1.0,
            nx: 20,
            ny: 20,
            dt: 0.001
        }
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleDomainChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            domain: {
                ...prev.domain,
                [name]: parseFloat(value)
            }
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form className="pde-form" onSubmit={handleSubmit}>
            <div className="form-group">
                <label htmlFor="equation">PDE Equation (LHS, e.g., uxx + uyy)</label>
                <input
                    type="text"
                    id="equation"
                    name="equation"
                    value={formData.equation}
                    onChange={handleChange}
                    required
                />
            </div>

            <div className="domain-grid">
                <h3>Domain Parameters</h3>

                <div className="form-group">
                    <label htmlFor="x_min">X Min</label>
                    <input
                        type="number"
                        id="x_min"
                        name="x_min"
                        step="any"
                        value={formData.domain.x_min}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="x_max">X Max</label>
                    <input
                        type="number"
                        id="x_max"
                        name="x_max"
                        step="any"
                        value={formData.domain.x_max}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="y_min">Y Min</label>
                    <input
                        type="number"
                        id="y_min"
                        name="y_min"
                        step="any"
                        value={formData.domain.y_min}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="y_max">Y Max</label>
                    <input
                        type="number"
                        id="y_max"
                        name="y_max"
                        step="any"
                        value={formData.domain.y_max}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="t_max">Time Max</label>
                    <input
                        type="number"
                        id="t_max"
                        name="t_max"
                        step="any"
                        value={formData.domain.t_max}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="dt">Time Step (dt)</label>
                    <input
                        type="number"
                        id="dt"
                        name="dt"
                        step="any"
                        value={formData.domain.dt}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="nx">Grid Points X (nx)</label>
                    <input
                        type="number"
                        id="nx"
                        name="nx"
                        value={formData.domain.nx}
                        onChange={handleDomainChange}
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="ny">Grid Points Y (ny)</label>
                    <input
                        type="number"
                        id="ny"
                        name="ny"
                        value={formData.domain.ny}
                        onChange={handleDomainChange}
                        required
                    />
                </div>
            </div>

            <div className="form-group">
                <label htmlFor="ic">Initial Condition (function of x, y)</label>
                <input
                    type="text"
                    id="ic"
                    name="ic"
                    value={formData.ic}
                    onChange={handleChange}
                    required
                    placeholder="e.g. sin(x)*cos(y)"
                />
            </div>

            <button type="submit" className="submit-btn" disabled={isLoading}>
                {isLoading ? 'Solving...' : 'Solve PDE'}
            </button>
        </form>
    );
};

export default PDEForm;
