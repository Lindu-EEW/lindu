import re

with open('src/dashboard-react/src/App.jsx', 'r') as f:
    content = f.read()

# Add import
content = content.replace("import NodeDetailModal from './components/NodeDetailModal';", "import NodeDetailModal from './components/NodeDetailModal';\nimport CommandCenterPanel from './components/CommandCenterPanel';")

# Extract sendCommand from hook
content = content.replace("const { isConnected, activeNodes, quakeDatabase, liveAlarm, setLiveAlarm, localMode, setLocalMode } = useMqtt();", "const { isConnected, activeNodes, quakeDatabase, liveAlarm, setLiveAlarm, localMode, setLocalMode, sendCommand } = useMqtt();")

# Inject right sidebar
right_sidebar = '''
      {/* Right Sidebar Layout */}
      <div className="absolute right-6 top-6 bottom-6 flex flex-col gap-4 z-[1000] pointer-events-none items-end">
        <CommandCenterPanel 
          activeNodes={activeNodes} 
          sendCommand={sendCommand} 
        />
      </div>
      
      <AlarmBanner'''

content = content.replace("      <AlarmBanner", right_sidebar)

with open('src/dashboard-react/src/App.jsx', 'w') as f:
    f.write(content)
