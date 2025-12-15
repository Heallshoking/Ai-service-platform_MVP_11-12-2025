import Header from '@/components/index/Header';
import ServicesTab from '@/components/index/ServicesTab';
import CalculatorTab from '@/components/index/CalculatorTab';
import OrderTab from '@/components/index/OrderTab';
import BottomNav from '@/components/index/BottomNav';
import { useIndexLogic } from '@/components/index/useIndexLogic';

const Index = () => {
  const {
    activeTab,
    setActiveTab,
    servicesList,
    executorsList,
    selectedExecutor,
    setSelectedExecutor,
    scenario,
    setScenario,
    repairType,
    setRepairType,
    calcType,
    setCalcType,
    switchCount,
    setSwitchCount,
    socketCount,
    setSocketCount,
    lightingType,
    setLightingType,
    powerEquipment,
    setPowerEquipment,
    installType,
    setInstallType,
    hasWires,
    setHasWires,
    phone,
    setPhone,
    address,
    setAddress,
    date,
    setDate,
    time,
    setTime,
    notes,
    setNotes,
    updateQuantity,
    getTotalPrice,
    getTotalItems,
    getCartItems,
    handleSubmit
  } = useIndexLogic();

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-6">
        {activeTab === 'home' && (
          <ServicesTab
            servicesList={servicesList}
            updateQuantity={updateQuantity}
          />
        )}

        {activeTab === 'calculator' && (
          <CalculatorTab
            scenario={scenario}
            setScenario={setScenario}
            repairType={repairType}
            setRepairType={setRepairType}
            calcType={calcType}
            setCalcType={setCalcType}
            switchCount={switchCount}
            setSwitchCount={setSwitchCount}
            socketCount={socketCount}
            setSocketCount={setSocketCount}
            lightingType={lightingType}
            setLightingType={setLightingType}
            powerEquipment={powerEquipment}
            setPowerEquipment={setPowerEquipment}
            installType={installType}
            setInstallType={setInstallType}
            hasWires={hasWires}
            setHasWires={setHasWires}
          />
        )}

        {activeTab === 'order' && (
          <OrderTab
            phone={phone}
            setPhone={setPhone}
            address={address}
            setAddress={setAddress}
            date={date}
            setDate={setDate}
            time={time}
            setTime={setTime}
            notes={notes}
            setNotes={setNotes}
            selectedExecutor={selectedExecutor}
            setSelectedExecutor={setSelectedExecutor}
            executorsList={executorsList}
            getCartItems={getCartItems}
            getTotalPrice={getTotalPrice}
            handleSubmit={handleSubmit}
          />
        )}
      </main>

      <BottomNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        getTotalItems={getTotalItems}
      />
    </div>
  );
};

export default Index;
