"""
    単位変換のためのモジュール
        by S.Sakai
    含まれるclass
        Convert: 全体を管理するクラス
        UnitBase: 単位変換のための基底クラス
    利用法: まずインスタンスを生成する
        from UnitCvrt import UnitConv as uc
        conv=uc.Convert()
    登録されている単位を確認する
        conv.Registered()
    1mをinに変換する場合
        conv.SetUnit('Length')
        conv.Eval('m','in',1)
        #39.37007874015748
"""
import numpy as np
class Convert:
    def __init__(self):
        self.unit=[
            'Length',
            'Nengo',
            'Temperature',
            'Force',
            'Stress',
            'Mass',
            'Moment',
            'Volume',
            'Density',
            'Pressure',
            'Acceleration',
            'Time',
            'Power',
            'Velecity',
            'Angle',
            'Area',
            'Sif',
            'Viscocity',
            'HeatConductivity',
            'HeatFlux',
            'HeatTransferRate',
            'UnitJ'            
        ]
        self.instance=None
    def Registered(self):
        '''
        登録されている単位名のリストを出力
        '''
        return self.unit
    def SetUnit(self,unit:str):
        '''
        対象とする単位名を文字列でセット
        '''
        cls=globals()[unit]
        if self.instance:
            del self.instance
        self.instance=cls()
        return self.instance
    def Eval(self,u1:str,u2:str,v:float)->float:
        '''
        vの数値をu1の文字列の単位からu2の文字列の単位に変換
        '''
        val=self.instance.Conv(u1,u2,v)
        return val
    def Table(self):
        '''
        単位の変換テーブルを出力する
        '''
        return self.instance.ShowDict()
    def DelUnit(self):
        '''
        内部で生成したインスタンスを消滅する
        '''
        del self.instance
    
class UnitBase:
    """ 単位変換のための基底クラス
    引数:
        unit_list: [('単位名称',変換係数)]のリスト
    含まれる関数:
        ShowDict: 変換係数テーブルの出力
        Conv:単位変換の関数
    """
    def __init__(self,unit_list):
        self.unit_dict={}
        self.number=len(unit_list)
        for unit_tuple in unit_list:
            (unit_name,val)=unit_tuple
            self.unit_dict[unit_name]=val
    def Coef(self,s):
        """ ストリングsの変換係数を返す
        引数:
            s: 単位区分の名称
        """
        return self.unit_dict[s]
    def Calc(self,v1,v2,v):
        """ 入力値vに対する変換後の数値を戻す
        v1: 変換単位区分1の係数
        v2: 変換単位区分2の係数
        v:  入力数値
        """
        return v*v1/v2
    def Conv(self,s1,s2,v):
        """ 単位変換の関数
        引数:
          s1: 変換元の単位名
          s2: 変換先の単位名
          v:  変換を行う数値
        """
        return self.Calc(self.Coef(s1),self.Coef(s2),v)
    def ShowDict(self):
        """項目名,数値　の辞書形式を返す
        """
        return self.unit_dict
    def ShowKeys(self):
        """単位項目名のリストを返す
        """
        tt=self.ShowDict()
        aa=tt.keys()
        return list(aa)        
class UnitBaseT(UnitBase):
    def __init__(self,unit_list):
        super().__init__(unit_list)
    def Calc(self,v1,v2,v):
        val1=0
        val2=0
        if v1==1.0:
            val1=v
        elif v1==2.0:
            val1 = (v-32.0)*5.0/9.0
        elif v1==0.0:
            val1=v-273.15
        if v2==1.0:
            val2=val1
        elif v2==2.0:
            val2=val1*9.0/5.0+32.0
        elif v2==0.0:
            val2=val1+273.15
        return val2
class UnitNengo(UnitBase):
    def __init__(self,unit_list):
        super().__init__(unit_list)
    def Calc(self,v1,v2,v):
        val1=val2=0.0
        Cur1=int(v1)
        Cur2=int(v2)
        if Cur1==0:
            val1=v+1867
        elif Cur1==1:
            val1=v+1911
        elif Cur1==2:
            val1=v+1925
        elif Cur1==3:
            val1=v+1988
        elif Cur1==4:
            val1=v+2018
        elif Cur1==5:
            val1=v
        if Cur2==0:
            val2=val1-1867
        elif Cur2==1:
            val2=val1-1911
        elif Cur2==2:
            val2=val1-1925
        elif Cur2==3:
            val2=val1-1988
        elif Cur2==4:
            val2=val1-2018
        elif Cur2==5:
            val2=val1
        return int(val2)
class Nengo(UnitNengo):
    def __init__(self):
        super().__init__([
            ('Meiji',0.0),
            ('Taisho',1.0),
            ('Syowa',2.0),
            ('Heisei',3.0),
            ('Reiwa',4.0),
            ('Seireki',5.0),
            ])
        

class Length(UnitBase):
    """
    単位:長さ
    項目:'m''cm''mm''in''feet''mile''yard''mils'
    """
    def __init__(self):
        super().__init__([
            ('m',1.0),
            ('cm',0.01),
            ('mm',0.001),
            ('in',0.02540),
            ('feet',12.0*0.02540),
            ('mile',1000.0*1.609),
            ('yard',1.0/1.094),
            ('mils',0.0254/1000.0)
            ])
class Temperature(UnitBaseT):
    """
    単位:温度
    項目:'K''Celsius''Fahrenheit'
    """
    def __init__(self):
        super().__init__([
            ('K',0.0),
            ('Celsius',1.0),
            ('Fahrenheit',2.0)
        ])
class Force(UnitBase):
    """
    単位:力
    項目:'N''gf''kgf''lb''klb''kip'
    """
    def __init__(self):
        super().__init__([
            ('N',1.0),
            ('gf',9.80665/1000.0),
            ('kgf',9.80665),
            ('lb',4.448222),
            ('klb',4.448222*1000),
            ('kip',4.448222*1000)
        ])
class Stress(UnitBase):
    """
    単位:応力
    項目:'Pa''GPa''MPa''kgf/cm2''kgf/mm2''psi''ksi''bar''N/m2''N/mm2'
    """
    def __init__(self):
        forc=Force()
        len=Length()
        super().__init__([
            ('Pa',1.0),
            ('GPa',1.0e9),
            ('MPa',1e6),
            ('kgf/cm2',forc.Coef('kgf')/len.Coef('cm')/len.Coef('cm')),
            ('kgf/mm2',forc.Coef('kgf')/len.Coef('mm')/len.Coef('mm')),
            ('psi',forc.Coef('lb')/len.Coef('in')/len.Coef('in')),
            ('ksi',forc.Coef('klb')/len.Coef('in')/len.Coef('in')),
            ('bar',1e5),
            ('N/m2',1.0),
            ('N/mm2',1e6)
        ])
class Mass(UnitBase):
    """
    単位:質量
    項目:'kg''g''lbm''slug'
    """
    def __init__(self):
        super().__init__([
            ('kg',1.0),
            ('g',0.001),
            ('lbm',0.45359237),
            ('slug',14.59390)
        ])
class Moment(UnitBase):
    """
    単位:モーメント
    項目:'N_m''gf_cm''lb_in''kip_feet'
    """
    def __init__(self):
        forc=Force()
        len=Length()
        super().__init__([
            ('N_m',1.0),
            ('gf_cm',forc.Coef('gf')*len.Coef('cm')),
            ('lb_in',forc.Coef('lb')*len.Coef('in')),
            ('kip_feet',forc.Coef('kip')*len.Coef('feet'))
        ])
class Volume(UnitBase):
    """
    単位:体積
    項目:'m^3''cm^3''in^3''feet^3''liter''gallon''barrel'
    """
    def __init__(self):
        len=Length()
        super().__init__([
            ('m^3',1.0),
            ('cm^3',len.Coef('cm')**3),
            ('mm^3',len.Coef('mm')**3),
            ('in^3',len.Coef('in')**3),
            ('feet^3',len.Coef('feet')**3),
            ('liter',1000*len.Coef('cm')**3),
            ('gallon',1000*len.Coef('cm')**3*3.785),
            ('barrel',1000*len.Coef('cm')**3*3.785*42.0)
        ])
class Density(UnitBase):
    """
    単位:密度
    項目:'N/m^3''kgf/cm^3''gf/cm^3''kgf/mm^3''lb/in^3''klb/feet^3'
    """
    def __init__(self):
        vol=Volume()
        forc=Force()
        super().__init__([
            ('N/m^3',1.0),
            ('kgf/cm^3',forc.Coef('kgf')/vol.Coef('cm^3')),
            ('gf/cm^3',forc.Coef('gf')/vol.Coef('cm^3')),
            ('kgf/mm^3',forc.Coef('kgf')/vol.Coef('mm^3')),
            ('lb/in^3',forc.Coef('lb')/vol.Coef('in^3')),
            ('klb/feet^3',forc.Coef('klb')/vol.Coef('feet^3'))
        ])
class Pressure(UnitBase):
    """
    単位:圧力
    項目:'Pa''bar''kgf/cm^2''atm''mmH2O''mmHg''lbf/in^2'
    """
    def __init__(self):
        super().__init__([
            ('Pa',1),
            ('bar',1e5),
            ('kgf/cm^2',9.80665e4),
            ('atm',1.01325e5),
            ('mmH2O',9.80665),
            ('mmHg',133.3224),
            ('lbf/in^2',6894.757)
        ])
class Acceleration(UnitBase):
    """
    単位:加速度
    項目:'Gal''mm/s^2''in/s^2''ft/s^2''m/s^2''G'
    """
    def __init__(self):
        super().__init__([
            ('Gal',1),
            ('mm/s^2',1/10),
            ('in/s^2',1/0.3937),
            ('ft/s^2',1/0.032808),
            ('m/s^2',100),
            ('G',980.665)
        ])
class Time(UnitBase):
    """
    単位:時間
    項目:'second''minute''hour''day''year'
    """
    def __init__(self):
        super().__init__({
            ('second',1.0),
            ('minute',60.0),
            ('hour',3600.0),
            ('day',86400.0),
            ('year',365.0*86400.0)
        })
class Power(UnitBase):
    """
    単位:パワー
    項目:'W''J/s''kgf_m/s''PS''ft_lbf/s'
    """
    def __init__(self):
        forc=Force()
        len=Length()
        tm=Time()
        super().__init__([
            ('W',1.0),
            ('J/s',1.0),
            ('kgf_m/s',forc.Coef('kgf')*len.Coef('m')/tm.Coef('second')),
            ('PS',735.4988),
            ('ft_lbf/s',forc.Coef('lb')*len.Coef('feet')/tm.Coef('second'))
        ])
class Velocity(UnitBase):
    """
    単位:速度
    項目:'m/s''km/h''ft/s''mph''mm/year''in/hr'
    """
    def __init__(self):
        len=Length()
        tm=Time()
        super().__init__({
            ('m/s',1.0),
            ('km/h',len.Coef('m')*1000.0/tm.Coef('hour')),
            ('ft/s',len.Coef('feet')/tm.Coef('second')),
            ('mph',len.Coef('mile')/tm.Coef('hour')),
            ('mpy',len.Coef('in')*0.001/tm.Coef('year')),
            ('mm/year',len.Coef('mm')/tm.Coef('year')),
            ('in/hr',len.Coef('in')/tm.Coef('hour')),
        })
class Angle(UnitBase):
    """ 
    単位:角度
    注意点: 'の表記は""で囲むこと
    項目:'rad''degree'"'""''"
    """
    def __init__(self):
        super().__init__({
            ('rad',1.0),
            ('degree',np.pi/180.0),
            ("'",np.pi/18/60),
            ("''",np.pi/18/60/60)
        })
class Area(UnitBase):
    """
    単位:面積
    項目:'m^2''cm^2''mm^2''in^2''feet^2''acre''hectare'
    """
    def __init__(self):
        len=Length()
        super().__init__({
            ('m^2',1.0),
            ('cm^2',len.Coef('cm')*len.Coef('cm')),
            ('mm^2',len.Coef('mm')*len.Coef('mm')),
            ('in^2',len.Coef('in')*len.Coef('in')),
            ('feet^2',len.Coef('feet')*len.Coef('feet')),
            ('acre',43560.0*len.Coef('feet')*len.Coef('feet')),
            ('hectare',10000.0)
        })
class Sif(UnitBase):
    """
    単位:応力拡大係数
    項目:'Pa_m^1/2''MPa_m^1/2''kgf/cm^3/2''kgf/mm^3/2''ksi/in^1/2'
    """
    def __init__(self):
        forc=Force()
        len=Length()
        super().__init__({
            ('Pa_m^1/2',1.0),
            ('MPa_m^1/2',1e6),
            ('N/mm^3/2',1/10**(-4.5)),
            ('N/m^3/2',forc.Coef('N')/len.Coef('m')/np.sqrt(len.Coef('m'))),
            ('kgf/cm^3/2',forc.Coef('kgf')/len.Coef('cm')/np.sqrt(len.Coef('cm'))),
            ('kgf/mm^3/2',forc.Coef('kgf')/len.Coef('mm')/np.sqrt(len.Coef('mm'))),
            ('ksi/in^1/2',forc.Coef('klb')/len.Coef('in')/np.sqrt(len.Coef('in'))),
            ('MPa_mm^1/2',1e6*np.sqrt(len.Coef('mm')))
        })
#### added at 2021.9.6        
class Viscocity(UnitBase):
    """
    単位:粘度
    項目:'Pa_s''kgf_s/m^2''lbf_s/ft^2''lbf_s/ft^2''lbm/(ft_s)''P''cP'
    """
    def __init__(self):
        super().__init__({
            ('Pa_s',1.0),
            ('kgf_s/m^2',9.80665),
            ('lbf_s/ft^2',4.788026),
            ('lbm/(ft_s)',1.488164),
            ('P',0.1),
            ('cP',0.001)
        })
class HeatConductivity(UnitBase):
    """
    単位:熱伝導率
    項目:'W/(m_K)''kcal/(m_h_celsius)''cal/(cm_s_celsius)''Btu/(ft_h_fahrenheit)'
    """
    def __init__(self):
        super().__init__({
            ('W/(m_K)',1.0),
            ('kcal/(m_h_celsius)',9.80665),
            ('cal/(cm_s_celsius)',4.788026),
            ('Btu/(ft_h_fahrenheit)',1.488164)
        })
class HeatFlux(UnitBase):
    """
    単位:熱流束
    項目:'W/m^2''kcal/(m^2_h)''Btu/(ft^2_h)'
    """
    def __init__(self):
        super().__init__({
            ('W/m^2',1.0),
            ('kcal/(m^2_h)',9.80665),
            ('Btu/(ft^2_h)',4.788026)
        })
class HeatTransferRate(UnitBase):
    """
    単位:熱伝達率
    項目:'W/(m^2_K)''kcal/(m^2_h_celsius)''Btu/(ft^2_h_fahrenheit)'
    """
    def __init__(self):
        super().__init__({
            ('W/(m^2_K)',1.0),
            ('kcal/(m^2_h_celsius)',1.163),
            ('Btu/(ft^2_h_fahrenheit)',5.678264)
        })
class UnitJ(UnitBase):
    """
    単位:J値
    項目:'W/(m^2_K)''kcal/(m^2_h_celsius)''Btu/(ft^2_h_fahrenheit)'

    """
    def __init__(self):
        forc=Force()
        len=Length()
        super().__init__({
            ('N/m',1.0),
            ('MN/m',1.163),
            ('kgf/m',5.678264),
            ('kgf/mm',forc.Coef('kgf')/len.Coef('mm')),
            ('lb/in',forc.Coef('lb')/len.Coef('in')),
            ('KJ/m^2',1000.0)
        })
class Rcheck:
    """適用範囲のチェック
    """
    def check(self,cond,val,min_r,max_r):
        if val >= min_r and val<=max_r:
            print('**Validation of [',cond,'] satisfied**')
            return
        print('**Validation of [',cond,'] not satisfied**:',',Value=',val)
