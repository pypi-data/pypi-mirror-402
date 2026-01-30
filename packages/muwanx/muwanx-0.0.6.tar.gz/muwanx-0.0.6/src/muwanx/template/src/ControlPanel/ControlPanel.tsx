import { Box, Menu, Select } from '@mantine/core';
import { IconChevronDown, IconRobot } from '@tabler/icons-react';
import FloatingPanel from './FloatingPanel';
import { LabeledInput } from './LabeledInput';

export interface SelectOption {
  value: string;
  label: string;
}

interface ControlPanelProps {
  projects: SelectOption[];
  projectValue: string | null;
  projectLabel: string;
  onProjectChange: (value: string | null) => void;
  scenes: SelectOption[];
  sceneValue: string | null;
  onSceneChange: (value: string | null) => void;
  menus: SelectOption[];
  menuValue: string | null;
  onMenuChange: (value: string | null) => void;
}

function ControlPanel(props: ControlPanelProps) {
  const {
    projects,
    projectValue,
    projectLabel,
    onProjectChange,
    scenes,
    sceneValue,
    onSceneChange,
    menus,
    menuValue,
    onMenuChange,
  } = props;

  // Only show panel if we have data to display
  if (!projects.length && !scenes.length && !menus.length) {
    return null;
  }

  return (
    <FloatingPanel width="20em">
      <FloatingPanel.Handle>
        <div style={{ width: "1.1em" }} />
        <IconRobot
          color="#228be6"
          style={{
            position: "absolute",
            width: "1.25em",
            height: "1.25em",
          }}
        />
        <FloatingPanel.HideWhenCollapsed>
          <Box
            px="xs"
            style={{
              flexGrow: 1,
              letterSpacing: "-0.5px",
              display: "flex",
              alignItems: "center",
              gap: "0.5em",
            }}
            pt="0.1em"
          >
            <span style={{ flexGrow: 1 }}>{projectLabel}</span>
            {projects.length > 1 && (
              <Menu position="bottom-start" offset={5}>
                <Menu.Target>
                  <Box
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                    }}
                  >
                    <IconChevronDown size={16} />
                  </Box>
                </Menu.Target>
                <Menu.Dropdown onClick={(e) => e.stopPropagation()}>
                  {projects.map((project) => (
                    <Menu.Item
                      key={project.value}
                      onClick={(e) => {
                        e.stopPropagation();
                        onProjectChange(project.value);
                      }}
                      style={{
                        fontWeight: project.value === projectValue ? 600 : 400,
                        backgroundColor:
                          project.value === projectValue
                            ? "rgba(34, 139, 230, 0.1)"
                            : undefined,
                      }}
                    >
                      {project.label}
                    </Menu.Item>
                  ))}
                </Menu.Dropdown>
              </Menu>
            )}
          </Box>
        </FloatingPanel.HideWhenCollapsed>
        <FloatingPanel.HideWhenExpanded>
          <Box px="xs" style={{ flexGrow: 1, letterSpacing: "-0.5px" }} pt="0.1em">
            {projectLabel}
          </Box>
        </FloatingPanel.HideWhenExpanded>
      </FloatingPanel.Handle>
      <FloatingPanel.Contents>
        <Box pt="0.375em">
          {scenes.length > 0 && (
            <LabeledInput id="scene-select" label="Scene">
              <Select
                id="scene-select"
                placeholder="Select scene"
                data={scenes}
                value={sceneValue}
                onChange={onSceneChange}
                size="xs"
                radius="xs"
                searchable
                clearable={false}
                styles={{
                  input: { minHeight: '1.625rem', height: '1.625rem', padding: '0.5em' },
                }}
                comboboxProps={{ zIndex: 1000 }}
              />
            </LabeledInput>
          )}

          {menus.length > 0 && (
            <LabeledInput id="policy-select" label="Policy">
              <Select
                id="policy-select"
                placeholder="Select policy"
                data={menus}
                value={menuValue}
                onChange={onMenuChange}
                size="xs"
                radius="xs"
                searchable
                clearable
                styles={{
                  input: { minHeight: '1.625rem', height: '1.625rem', padding: '0.5em' },
                }}
                comboboxProps={{ zIndex: 1000 }}
              />
            </LabeledInput>
          )}
        </Box>
      </FloatingPanel.Contents>
    </FloatingPanel>
  );
}

export default ControlPanel;
