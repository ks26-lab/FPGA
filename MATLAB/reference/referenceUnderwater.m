function result = referenceUnderwater(inputData)
% REFERENCEUNDERWATER Golden reference mathematical model for underwater depth control.
%
% Architecture Role:
%   Acts as the validated mathematical reference against which the FPGA hardware
%   implementation is compared. Uses double-precision floating point (float64).
%
% Mathematical Model:
%   1. Filtering:
%      filteredDepth = exponentialFilter(rawDepth, alpha)
%   2. Hydrostatic Conversion (if pressure provided):
%      h_hydro = (P - P0) / (rho * g)
%   3. Error Calculation:
%      depthError = targetDepth - filteredDepth
%   4. PD Ballast / Vertical Thrust Control:
%      pTerm = Kp * depthError
%      dTerm = -Kd * velocity
%      rawControl = 50.0 + pTerm + dTerm
%      controlOutput = clamp(rawControl, 0.0, 100.0)
%   5. Operational State Machine:
%      depthError > 0.5  => "DESCENDING"
%      depthError < -0.5 => "ASCENDING"
%      otherwise         => "HOLDING"
%
% Inputs:
%   inputData - struct containing:
%                 .depth        (required, meters)
%                 .targetDepth  (optional, default = 50.0 m)
%                 .velocity     (optional, default = 0.0 m/s)
%                 .pressure     (optional, kPa)
%                 .weight       (optional, kg)
%                 .fluidDensity (optional, kg/m^3)
%                 .filterAlpha  (optional, default = 0.25)
%
% Output:
%   result - struct conforming to golden reference contract with:
%              .scene ("underwater_depth")
%              .status ("OK")
%              .outputs (depth, controlOutput, state, ...)
%              .intermediate (rawDepth, filteredDepth, error, pTerm, dTerm, ...)
%              .parameters (Kp, Kd, alpha, rho, g)
%              .precision ("float64")

    % Physical and control parameters (explicitly defined)
    Kp = 1.25;          % Proportional gain (control % per meter error)
    Kd = 0.50;          % Derivative / damping gain (control % per m/s)
    g  = 9.80665;       % Standard gravity (m/s^2)
    P0 = 101.325;       % Atmospheric pressure at sea level (kPa)

    % Extract / default inputs
    rawDepth = double(inputData.depth);
    if length(rawDepth) > 1, d_in = rawDepth(end); else, d_in = rawDepth; end

    if isfield(inputData, 'targetDepth') && ~isempty(inputData.targetDepth)
        targetDepth = double(inputData.targetDepth);
    else
        targetDepth = 50.0; % Nominal target depth in meters
    end

    if isfield(inputData, 'velocity') && ~isempty(inputData.velocity)
        rawVel = double(inputData.velocity);
        if length(rawVel) > 1, vel = rawVel(end); else, vel = rawVel; end
    else
        vel = 0.0;
    end

    if isfield(inputData, 'filterAlpha') && ~isempty(inputData.filterAlpha)
        alpha = double(inputData.filterAlpha);
    else
        alpha = 0.25; % FPGA bit-shift friendly (2^-2)
    end

    if isfield(inputData, 'fluidDensity') && ~isempty(inputData.fluidDensity)
        rho = double(inputData.fluidDensity);
    else
        rho = 1025.0; % Seawater density (kg/m^3)
    end

    % 1. Stage 1: Filtering
    if length(rawDepth) > 1
        filteredArr = exponentialFilter(rawDepth, alpha);
        filteredDepth = filteredArr(end);
    else
        filteredDepth = alpha * d_in + (1.0 - alpha) * d_in; % Steady-state scalar
    end

    % 2. Stage 2: Hydrostatic Pressure Conversion (if pressure supplied)
    hydroDepth = 0.0;
    hasPressure = isfield(inputData, 'pressure') && ~isempty(inputData.pressure);
    if hasPressure
        rawP = double(inputData.pressure);
        if length(rawP) > 1, p_val = rawP(end); else, p_val = rawP; end
        hydroDepth = max(0.0, ((p_val - P0) * 1000.0) / (rho * g));
    end

    % 3. Stage 3: Error Calculation
    depthError = targetDepth - filteredDepth;

    % 4. Stage 4: Control Calculation
    pTerm = Kp * depthError;
    dTerm = -Kd * vel;
    rawControl = 50.0 + pTerm + dTerm;
    controlOutput = max(0.0, min(100.0, rawControl));

    % 5. Stage 5: State Machine
    if depthError > 0.5
        stateStr = "DESCENDING";
    elseif depthError < -0.5
        stateStr = "ASCENDING";
    else
        stateStr = "HOLDING";
    end

    % Package Outputs conforming to reference model contract
    outputs = struct();
    outputs.depth = filteredDepth;
    outputs.controlOutput = controlOutput;
    outputs.state = stateStr;
    if hasPressure
        outputs.hydrostaticDepth = hydroDepth;
    end

    % Intermediate values for granular stage-by-stage FPGA debugging
    intermediate = struct();
    intermediate.rawDepth = d_in;
    intermediate.filteredDepth = filteredDepth;
    intermediate.targetDepth = targetDepth;
    intermediate.depthError = depthError;
    intermediate.velocity = vel;
    intermediate.proportionalTerm = pTerm;
    intermediate.derivativeTerm = dTerm;
    intermediate.rawControlOutput = rawControl;

    parameters = struct( ...
        'Kp', Kp, ...
        'Kd', Kd, ...
        'filterAlpha', alpha, ...
        'fluidDensity', rho, ...
        'gravity', g, ...
        'P0', P0);

    result = struct( ...
        'scene', "underwater_depth", ...
        'status', "OK", ...
        'outputs', outputs, ...
        'intermediate', intermediate, ...
        'parameters', parameters, ...
        'precision', "float64");
end
