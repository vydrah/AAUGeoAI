@echo off
echo Compiling resources...
pyrcc5 resources.qrc -o resources.py

echo Compiling UI files...
pyuic5 wizard/wizard.ui -o wizard/wizard_ui.py
pyuic5 wizard/step_algorithm.ui -o wizard/step_algorithm_ui.py
pyuic5 wizard/step_parameters.ui -o wizard/step_parameters_ui.py
pyuic5 wizard/step_roi.ui -o wizard/step_roi_ui.py
pyuic5 wizard/step_bands.ui -o wizard/step_bands_ui.py
pyuic5 wizard/step_llm.ui -o wizard/step_llm_ui.py
pyuic5 wizard/step_output.ui -o wizard/step_output_ui.py
pyuic5 ui/dockwidget.ui -o ui/dockwidget_ui.py

echo Done!
pause
