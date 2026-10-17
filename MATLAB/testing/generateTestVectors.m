function testVectors = generateTestVectors(outputJsonPath)
% GENERATETESTVECTORS Generates deterministic test vectors for MATLAB & FPGA validation.
%
% Architecture Role:
%   Generates identical test stimulus vectors sent simultaneously to:
%     1. MATLAB Golden Reference Model
%     2. Zynq FPGA Hardware / Simulator
%
% Covered Test Scenarios:
%    1. Normal input (nominal operating point)
%    2. Minimum input (zero boundary)
%    3. Maximum input (physical upper limit)
%    4. Zero input (physically valid zero velocity / zero delta)
%    5. Noisy input (simulated sensor noise vector)
%    6. Outlier input (isolated sensor glitch spike)
%    7. Boundary condition (threshold crossing e.g. state transition point)
%    8. Multi-scene: Traffic scene
%    9. Multi-scene: Space Habitat scene
%   10. Numerical precision / micro-step input
%
% Syntax:
%   testVectors = generateTestVectors(outputJsonPath)

    if nargin < 1 || isempty(outputJsonPath)
        outputJsonPath = '';
    end

    testVectors = struct('id', {}, 'name', {}, 'scene', {}, 'input', {}, 'description', {});

    % Vector 1: Normal Input (Underwater)
    testVectors(1).id = 1;
    testVectors(1).name = "Normal_Underwater_Descent";
    testVectors(1).scene = "underwater_depth";
    testVectors(1).input = struct('scene', "underwater_depth", 'depth', 45.0, 'targetDepth', 50.0, 'velocity', 1.2, 'weight', 75.0, 'height', 10.0);
    testVectors(1).description = "Nominal underwater probe descent approaching target depth";

    % Vector 2: Minimum Input (Surface Boundary)
    testVectors(2).id = 2;
    testVectors(2).name = "Minimum_Boundary_Surface";
    testVectors(2).scene = "underwater_depth";
    testVectors(2).input = struct('scene', "underwater_depth", 'depth', 0.0, 'targetDepth', 50.0, 'velocity', 0.0, 'weight', 50.0, 'height', 0.0);
    testVectors(2).description = "Zero depth at surface with stationary initial condition";

    % Vector 3: Maximum Input (Deep Ocean)
    testVectors(3).id = 3;
    testVectors(3).name = "Maximum_Boundary_Deep";
    testVectors(3).scene = "underwater_depth";
    testVectors(3).input = struct('scene', "underwater_depth", 'depth', 10900.0, 'targetDepth', 10920.0, 'velocity', 2.0, 'weight', 1200.0, 'height', 5.0);
    testVectors(3).description = "Extreme oceanic trench depth boundary condition";

    % Vector 4: Zero Input / State Holding
    testVectors(4).id = 4;
    testVectors(4).name = "Zero_Error_Holding";
    testVectors(4).scene = "underwater_depth";
    testVectors(4).input = struct('scene', "underwater_depth", 'depth', 50.0, 'targetDepth', 50.0, 'velocity', 0.0, 'weight', 75.0, 'height', 10.0);
    testVectors(4).description = "Exact target match verifying zero steady-state error and HOLDING state";

    % Vector 5: Noisy Input Series
    testVectors(5).id = 5;
    testVectors(5).name = "Noisy_Sensor_Stream";
    testVectors(5).scene = "underwater_depth";
    testVectors(5).input = struct('scene', "underwater_depth", 'depth', [48.0, 52.0, 47.5, 51.5, 49.0], 'targetDepth', 50.0, 'velocity', 0.5, 'filterAlpha', 0.25);
    testVectors(5).description = "5-sample noisy sensor burst verifying filter smoothing";

    % Vector 6: Outlier Input
    testVectors(6).id = 6;
    testVectors(6).name = "Impulsive_Sensor_Outlier";
    testVectors(6).scene = "underwater_depth";
    testVectors(6).input = struct('scene', "underwater_depth", 'depth', [50.0, 50.1, 450.0, 50.2, 50.0], 'targetDepth', 50.0, 'velocity', 0.0, 'filterAlpha', 0.25);
    testVectors(6).description = "Single corrupted telemetry spike testing outlier attenuation";

    % Vector 7: Boundary Crossing (Ascent vs Descent)
    testVectors(7).id = 7;
    testVectors(7).name = "Ascending_Overshoot";
    testVectors(7).scene = "underwater_depth";
    testVectors(7).input = struct('scene', "underwater_depth", 'depth', 65.0, 'targetDepth', 50.0, 'velocity', -1.5, 'weight', 75.0, 'height', 10.0);
    testVectors(7).description = "Probe below target executing ascent recovery";

    % Vector 8: Traffic Scene (Congestion)
    testVectors(8).id = 8;
    testVectors(8).name = "Traffic_Intersection_Congestion";
    testVectors(8).scene = "traffic";
    testVectors(8).input = struct('scene', "traffic", 'velocity', 3.5, 'queueLength', 24.0);
    testVectors(8).description = "Slow vehicle flow (12.6 km/h) with heavy queue allocating maximum green";

    % Vector 9: Space Habitat Scene (Nominal Life Support)
    testVectors(9).id = 9;
    testVectors(9).name = "Space_Habitat_Pressure_Drop";
    testVectors(9).scene = "space_habitat";
    testVectors(9).input = struct('scene', "space_habitat", 'pressure', 98.5, 'temperature', 19.5, 'targetPressure', 101.325, 'targetTemp', 21.0);
    testVectors(9).description = "Habitat minor atmospheric pressure drop triggering valve actuation";

    % Vector 10: Numerical Micro-Precision Case
    testVectors(10).id = 10;
    testVectors(10).name = "Micro_Precision_Delta";
    testVectors(10).scene = "underwater_depth";
    testVectors(10).input = struct('scene', "underwater_depth", 'depth', 49.9998, 'targetDepth', 50.0, 'velocity', 0.0001, 'weight', 75.0, 'height', 10.0);
    testVectors(10).description = "Sub-millimeter error testing float64 vs fixed-point quantization limits";

    % Optional JSON export
    if ~isempty(outputJsonPath)
        fid = fopen(outputJsonPath, 'w');
        if fid ~= -1
            fwrite(fid, jsonencode(testVectors, 'PrettyPrint', true));
            fclose(fid);
            fprintf('[INFO] Exported %d test vectors to %s\n', length(testVectors), outputJsonPath);
        end
    end
end
