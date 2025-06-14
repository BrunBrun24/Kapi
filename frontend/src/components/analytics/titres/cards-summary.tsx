"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

type StockStatisticsCardProps = {
  title: string;
  height: number;
};

export function StockStatisticsCard({
  title,
  height,
}: StockStatisticsCardProps) {
  return (
    <Card style={{ height: `${height}px` }} className="flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-2xl font-bold">{title}</CardTitle>
        <p className="text-sm text-muted-foreground">Actions uniquement</p>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-4 text-sm">
        {/* Général */}
        <div>
          <h4 className="font-medium mb-2">Général</h4>
          <div className="mb-1">
            Nombre d’actions: <strong>15</strong>
          </div>
          <div className="mb-1">
            Market Cap: <strong>707 832,94 M$</strong>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Note Q:</div>
            <div className="w-[60px] text-right font-semibold">16,56</div>
            <Progress value={16.56} className="flex-1 h-2" />
          </div>
        </div>

        {/* Retours sur capitaux */}
        <div>
          <h4 className="font-medium mb-2">Retours sur capitaux</h4>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">ROIC:</div>
            <div className="w-[60px] text-right font-semibold">28,88%</div>
            <Progress value={28.88} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">ROCE:</div>
            <div className="w-[60px] text-right font-semibold">36,71%</div>
            <Progress value={36.71} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">ROE:</div>
            <div className="w-[60px] text-right font-semibold">101,31%</div>
            <Progress value={100} className="flex-1 h-2" />
          </div>
        </div>

        {/* Santé */}
        <div>
          <h4 className="font-medium mb-2">Santé</h4>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Dettes/EBITDA:</div>
            <div className="w-[60px] text-right font-semibold">0,78</div>
            <Progress value={0.78} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Interests Coverage:</div>
            <div className="w-[60px] text-right font-semibold">173,65</div>
            <Progress value={100} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2 text-red-600">
            <div className="w-[110px] text-left">Goodwill/Assets:</div>
            <div className="w-[60px] text-right font-semibold">13,48%</div>
            <Progress value={13.48} className="flex-1 h-2 bg-red-500" />
          </div>
        </div>

        {/* Marges */}
        <div>
          <h4 className="font-medium mb-2">Marges</h4>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Marge brute:</div>
            <div className="w-[60px] text-right font-semibold">60,28%</div>
            <Progress value={60.28} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Marge opérationnelle:</div>
            <div className="w-[60px] text-right font-semibold">40,53%</div>
            <Progress value={40.53} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2">
            <div className="w-[110px] text-left">Marge nette:</div>
            <div className="w-[60px] text-right font-semibold">33,83%</div>
            <Progress value={33.83} className="flex-1 h-2" />
          </div>
        </div>

        {/* Croissance */}
        <div>
          <h4 className="font-medium mb-2">Croissance</h4>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Croissance revenus:</div>
            <div className="w-[60px] text-right font-semibold">13,29%</div>
            <Progress value={13.29} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2 mb-2">
            <div className="w-[110px] text-left">Croissance BPA:</div>
            <div className="w-[60px] text-right font-semibold">17,81%</div>
            <Progress value={17.81} className="flex-1 h-2" />
          </div>

          <div className="flex items-center gap-2">
            <div className="w-[110px] text-left">Croissance FCF:</div>
            <div className="w-[60px] text-right font-semibold">28,47%</div>
            <Progress value={28.47} className="flex-1 h-2" />
          </div>
        </div>

        {/* Évaluation */}
        <div>
          <h4 className="font-medium mb-2">Évaluation</h4>
          <div className="mb-1">
            P/E Ratio: <strong>30,87</strong>
          </div>
          <div className="mb-1">
            P/E sur coût: <strong>24,85</strong>
          </div>
          <div className="mb-1">
            P/FCF Ratio: <strong>31,02</strong>
          </div>
          <div className="mb-1">
            P/FCF sur coût: <strong>25</strong>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
