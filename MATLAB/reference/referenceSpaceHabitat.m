function result = referenceSpaceHabitat(inputData)
% REFERENCESPACEHABITAT Golden reference mathematical model for space habitat life-support.
%
% Mathematical Model:
%   1. Filter Atmospheric Inputs:
%      P_filt = exponentialFilter(P_raw, alpha)
%      T_filt = exponentialFilter(T_raw, alpha)
%   2. Life-Support Error Calculations:
%      e_P = targetPressure - P_filt
%      e_T = targetTemp - T_filt
%   3. Valve / Environmental Actuation:
%      pressureValve = clamp(50.0 + Kp_P * e_P, 0.0, 100.0)
%      thermalControl = clamp(50.0 + Kp_T * e_T, 0.0, 100.0)
%   4. Safety State:
%      |e_P| >= 5.0 or |e_T| >= 10.0 => "CRITICAL"
%      |e_P| >= 1.0 or |e_T| >= 2.0  => "WARNING"
%      otherwise                     => "NOMINAL"

    Kp_P = 10.0; % Valve response (% per kPa)
    Kp_T = 5.0;  % Thermal response (% per degC)
    alpha = 0.25;

    rawP = double(inputData.pressure);
    if length(rawP) > 1, p_in = rawP(end); else, p_in = rawP; end

    if isfield(inputData, 'temperature') && ~isempty(inputData.temperature)
        rawT = double(inputData.temperature);
        if length(rawT) > 1, t_in = rawT(end); else, t_in = rawT; end
    else
        t_in = 21.0;
    end

    if isfield(inputData, 'targetPressure') && ~isempty(inputData.targetPressure)
        targetP = double(inputData.targetPressure);
    else
        targetP = 101.325; % Nominal Earth atmosphere in habitat
    end

    if isfield(inputData, 'targetTemp') && ~isempty(inputData.targetTemp)
        targetT = double(inputData.targetTemp);
    else
        targetT = 21.0; % 21 degC nominal
    end

    % 1. Filter
    if length(rawP) > 1
        fP_arr = exponentialFilter(rawP, alpha);
        p_filt = fP_arr(end);
    else
        p_filt = p_in;
    end

    t_filt = t_in;

    % 2. Errors
    e_P = targetP - p_filt;
    e_T = targetT - t_filt;

    % 3. Actuation
    rawValve = 50.0 + Kp_P * e_P;
    pressureValve = max(0.0, min(100.0, rawValve));

    rawThermal = 50.0 + Kp_T * e_T;
    thermalControl = max(0.0, min(100.0, rawThermal));

    % 4. State
    if abs(e_P) >= 5.0 || abs(e_T) >= 10.0
        stateStr = "CRITICAL";
    elseif abs(e_P) >= 1.0 || abs(e_T) >= 2.0
        stateStr = "WARNING";
    else
        stateStr = "NOMINAL";
    end

    outputs = struct();
    outputs.filteredPressure = p_filt;
    outputs.filteredTemperature = t_filt;
    outputs.pressureValve = pressureValve;
    outputs.thermalControl = thermalControl;
    outputs.state = stateStr;

    intermediate = struct();
    intermediate.rawPressure = p_in;
    intermediate.filteredPressure = p_filt;
    intermediate.pressureError = e_P;
    intermediate.thermalError = e_T;
    intermediate.rawPressureValve = rawValve;
    intermediate.rawThermalControl = rawThermal;

    parameters = struct( ...
        'Kp_P', Kp_P, ...
        'Kp_T', Kp_T, ...
        'targetPressure', targetP, ...
        'targetTemp', targetT, ...
        'filterAlpha', alpha);

    result = struct( ...
        'scene', "space_habitat", ...
        'status', "OK", ...
        'outputs', outputs, ...
        'intermediate', intermediate, ...
        'parameters', parameters, ...
        'precision', "float64");
end
