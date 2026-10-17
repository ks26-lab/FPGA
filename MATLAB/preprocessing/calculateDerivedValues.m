function derived = calculateDerivedValues(inputData, filteredResults)
% CALCULATEDERIVEDVALUES Computes domain-specific derived values for FPGA consumption.
%
% Keeps derived/physical conversions cleanly separate from filtering.
%
% Supported Computations:
%   - Hydrostatic depth from pressure (if pressure and fluid properties are provided)
%   - Depth change rate (vertical velocity estimate)
%   - Kinetic energy (if weight and velocity are provided)
%   - Normalized signal representation ready for fixed-point quantization
%
% Inputs:
%   inputData       - Raw input struct from Python
%   filteredResults - Struct containing results from filtering functions
%
% Outputs:
%   derived         - Struct of derived values (numerical and serializable)

    derived = struct();
    sceneName = string(inputData.scene);

    switch sceneName
        case "underwater_depth"
            % 1. Vertical Velocity Estimate from filtered depth
            if isfield(filteredResults, 'depth')
                fDepth = filteredResults.depth.filteredDepth;
                if length(fDepth) > 1
                    % Vector of samples
                    dt = 0.1; % Default sample interval 100ms if timestamp not specified
                    if isfield(inputData, 'timestamp') && length(inputData.timestamp) > 1
                        dt = mean(diff(inputData.timestamp));
                        if dt <= 0, dt = 0.1; end
                    end
                    derived.verticalVelocity = (fDepth(end) - fDepth(1)) / (length(fDepth) * dt);
                else
                    derived.verticalVelocity = 0.0;
                end
            end

            % 2. Hydrostatic Depth Calculation (only if pressure is provided and caller specifies density)
            % Formula: h = (P - P0) / (rho * g)
            if isfield(inputData, 'pressure') && isfield(inputData, 'fluidDensity')
                P = double(inputData.pressure);    % in kPa
                rho = double(inputData.fluidDensity); % in kg/m^3 (e.g. 1025 for seawater, 1000 for freshwater)
                g = 9.80665;                       % gravitational acceleration m/s^2
                P0 = 101.325;                      % Standard sea level atmospheric pressure in kPa
                
                % Convert (kPa -> Pa): 1 kPa = 1000 Pa = 1000 N/m^2
                hydroDepth = ((P - P0) * 1000.0) / (rho * g);
                derived.hydrostaticDepthCalculated = max(0.0, hydroDepth);
                derived.fluidDensityUsed = rho;
            end

            % 3. Kinetic Energy: E = 0.5 * m * v^2
            if isfield(inputData, 'weight') && isfield(filteredResults, 'velocity')
                m = double(inputData.weight);
                v = double(filteredResults.velocity.filteredVelocity);
                if length(v) > 1, v_eff = v(end); else, v_eff = v; end
                derived.kineticEnergyJoules = 0.5 * m * (v_eff ^ 2);
            end

            % 4. Normalized Primary Signal (Depth) for FPGA integer/fixed-point scaling
            if isfield(filteredResults, 'depth')
                dVal = filteredResults.depth.filteredDepth;
                [normD, p] = normalizeData(dVal, 0.0, 11000.0);
                derived.normalizedDepth = normD;
                derived.depthNormRange = [p.min, p.max];
            end

        case "solar_tracker"
            if isfield(filteredResults, 'velocity')
                vVal = filteredResults.velocity.filteredVelocity;
                [normV, p] = normalizeData(vVal, -10.0, 10.0);
                derived.normalizedVelocity = normV;
                derived.velocityNormRange = [p.min, p.max];
            end

        case "mars_atmospheric"
            if isfield(filteredResults, 'pressure') && isfield(filteredResults, 'temperature')
                P = filteredResults.pressure.filteredPressure;
                T = filteredResults.temperature.filteredTemperature;
                % Mars atmospheric density estimate: rho = P / (R_specific * T_kelvin)
                % R_specific for CO2 = 188.9 J/(kg*K)
                if length(P) > 1, P_eff = P(end); else, P_eff = P; end
                if length(T) > 1, T_eff = T(end); else, T_eff = T; end
                T_k = T_eff + 273.15;
                if T_k > 0
                    derived.atmosphericDensityEst = (P_eff * 1000.0) / (188.9 * T_k);
                end
            end

        case "smart_city"
            if isfield(filteredResults, 'velocity')
                v = filteredResults.velocity.filteredVelocity;
                if length(v) > 1, v_cur = v(end); else, v_cur = v; end
                derived.speedKmh = v_cur * 3.6;
            end
    end
end
