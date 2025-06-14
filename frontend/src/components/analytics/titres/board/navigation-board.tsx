import React, { useState } from 'react';
import { BoardPositionsTickers } from "@/components/analytics/titres/board/positions/board-position-tickers";
import { BoardTransactions } from "@/components/analytics/titres/board/transactions/board-ticker-transaction";
import { IconStackFront } from '@tabler/icons-react';
import { List } from 'lucide-react';

export const NavBar: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'positions' | 'transactions'>('positions');

  const baseTabStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    cursor: 'pointer',
    fontWeight: 'bold',
    paddingBottom: '4px',
  };

  return (
    <div>
      <nav style={{ display: 'flex', gap: '20px' }}>
        <div
          role="button"
          tabIndex={0}
          onClick={() => setActiveTab('positions')}
          style={{
            ...baseTabStyle,
            color: activeTab === 'positions' ? 'blue' : 'black',
            borderBottom: activeTab === 'positions' ? '2px solid blue' : 'none',
          }}
        >
          <IconStackFront size={20} /> Positions
        </div>
        <div
          role="button"
          tabIndex={0}
          onClick={() => setActiveTab('transactions')}
          style={{
            ...baseTabStyle,
            color: activeTab === 'transactions' ? 'blue' : 'black',
            borderBottom: activeTab === 'transactions' ? '2px solid blue' : 'none',
          }}
        >
          <List size={20} /> Transactions
        </div>
      </nav>

      <div style={{ marginTop: '20px' }}>
        {activeTab === 'positions' ? <BoardPositionsTickers /> : <BoardTransactions />}
      </div>
    </div>
  );
};
