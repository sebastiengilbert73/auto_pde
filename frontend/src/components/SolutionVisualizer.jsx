import React, { useState, useEffect } from 'react';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';

const Plot = createPlotlyComponent(Plotly);

const SolutionVisualizer = ({ solution }) => {
    const [frameIndex, setFrameIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const { x, y, t, frames } = solution;

    useEffect(() => {
        let interval;
        if (isPlaying) {
            interval = setInterval(() => {
                setFrameIndex((prev) => (prev + 1) % frames.length);
            }, 100); // 100ms per frame
        }
        return () => clearInterval(interval);
    }, [isPlaying, frames.length]);

    const currentFrame = frames[frameIndex];

    // Prepare data for Plotly
    // Plotly Surface expects z to be a 2D array [y][x]
    // Our backend returns frames as [y][x] (numpy default)

    const data = [
        {
            z: currentFrame,
            x: x,
            y: y,
            type: 'surface',
            colorscale: 'Viridis',
            showscale: true,
            contours: {
                z: {
                    show: true,
                    usecolormap: true,
                    highlightcolor: "#42f462",
                    project: { z: true }
                }
            }
        }
    ];

    // Calculate global min and max for all axes to keep scale fixed
    const allValues = frames.flat().flat();
    const zMin = Math.min(...allValues);
    const zMax = Math.max(...allValues);
    // Add some padding
    const zRange = zMax - zMin;
    const padding = zRange * 0.1 || 0.1; // Default padding if range is 0

    const layout = {
        title: `Solution at t = ${t[frameIndex].toFixed(3)}`,
        autosize: true,
        width: 800,
        height: 600,
        scene: {
            xaxis: {
                title: 'X',
                range: [x[0], x[x.length - 1]],
                autorange: false
            },
            yaxis: {
                title: 'Y',
                range: [y[0], y[y.length - 1]],
                autorange: false
            },
            zaxis: {
                title: 'u(x,y,t)',
                range: [zMin - padding, zMax + padding],
                autorange: false
            },
            camera: {
                eye: { x: 1.5, y: 1.5, z: 1.5 }
            },
            aspectmode: 'cube'
        },
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 50,
        }
    };

    return (
        <div className="visualizer-container" style={{ marginTop: '2rem', textAlign: 'center' }}>
            <Plot
                data={data}
                layout={layout}
                useResizeHandler={true}
                style={{ width: '100%', height: '100%' }}
            />

            <div className="controls" style={{ marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center', alignItems: 'center' }}>
                <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    style={{
                        padding: '0.5rem 1rem',
                        backgroundColor: isPlaying ? '#ef4444' : '#22c55e',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }}
                >
                    {isPlaying ? 'Pause' : 'Play'}
                </button>

                <input
                    type="range"
                    min="0"
                    max={frames.length - 1}
                    value={frameIndex}
                    onChange={(e) => {
                        setIsPlaying(false);
                        setFrameIndex(parseInt(e.target.value));
                    }}
                    style={{ width: '300px' }}
                />
                <span>Frame: {frameIndex} / {frames.length - 1}</span>
            </div>
        </div>
    );
};

export default SolutionVisualizer;
