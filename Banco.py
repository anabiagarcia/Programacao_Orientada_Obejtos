from dataclasses import dataclass, field
from typing import List
import datetime
from enum import Enum

class BankError(Exception):
    def __init__(self, message: str = "Um erro ocorreu no sistema do banco"):
        super().__init__(message)

class NonClientError(BankError):
    def __init__(self, member_name: str):
        message = f"{member_name} nao e cliente"
        super().__init__(message)

class NonCountError(NonClientError):
    def __init__(self, conta: 'Conta'):
        message = f"A conta {conta.numero} nao existe"
        super().__init__(message)

class OperationError(Exception):
    def __init__(self, message: str = "Operação Inválida"):
        super().__init__(message)

@dataclass
class Endereco:
    rua: str
    numero: int
    bairro: str
    cidade: str
    estado: str
    cep: str

@dataclass
class Cliente:
    nome: str
    cpf: str
    enderecos: List[Endereco] = field(default_factory=list)
    contas: List['Conta'] = field(default_factory=list)
    
    def adicionar_conta(self, conta: 'Conta'):
        self.contas.append(conta)

    def remover_conta(self, numero_conta: str) -> bool:
        for conta in self.contas:
            if conta.numero == numero_conta:
                self.contas.remove(conta)
                return True
        return False
    
    def listar_contas(self):
        return self.contas

@dataclass
class Conta:
    titular: Cliente
    saldo: float
    numero: str
    saques_diarios: int = 0 
    limite_saques_diarios: int = 20
    operacoes: List['Operacao'] = field(default_factory=list)
    ultima_atualizacao: datetime.date = field(default_factory=datetime.date.today)

    def debitar(self, valor: float) -> bool:
        if valor > self.saldo and isinstance(self, Corrente):
            return self.debitar_com_cheque_especial(valor)
        elif valor > self.saldo:
            return False      
        self.saldo -= valor
        return True

    def creditar(self, valor: float):
        self.saldo += valor

    def historico(self):
         return self.operacoes
    
    def verificar_reset(self):
        data_atual = datetime.date.today()
        
        if data_atual != self.ultima_atualizacao:
            self.saques_diarios = 0 
            self.ultima_atualizacao = data_atual


    def limite_saque(self):
        self.verificar_reset()
        if isinstance(self, Poupanca):
            return self.saques_diarios < self.limite_saques_diarios
        return True
        
            
class Corrente(Conta):
    def __init__(self, titular: 'Cliente', saldo: float, numero: str):
        super().__init__(titular, saldo, numero)

    limite_cheque_especial: float = 5000.0

    def debitar_com_cheque_especial(self, valor: float) -> bool:
        if valor > self.limite_cheque_especial + self.saldo:
            return False      
        self.limite_cheque_especial -= (valor - self.saldo)
        self.saldo = 0.0
        return True


class Poupanca(Conta):
    def __init__(self, titular: 'Cliente', saldo: float, numero: str):
        super().__init__(titular, saldo, numero)

    taxa_rendimento: float = 0.001

    def aplicar_rendimentos(self):
        self.saldo *= (1 + self.taxa_rendimento)

class TipoOperacao(Enum):
    DEPOSITO = "Depósito"
    SAQUE = "Saque"
    TRANSFERENCIA_DEBITO = "Transferência - Débito"
    TRANSFERENCIA_CREDITO = "Transferência - Crédito"

@dataclass
class Operacao:
    tipo: TipoOperacao 
    valor: float
    dia: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class Banco:
    clientes: List[Cliente] = field(default_factory=list)
    contas: List[Conta] = field(default_factory=list)

    def criar_cliente(self, novo_cliente: Cliente):
        self.clientes.append(novo_cliente)
    
    def nova_conta(self, cliente: Cliente, conta: Conta):
        if cliente not in self.clientes:
            raise NonClientError(cliente.nome)
        self.contas.append(conta)
        cliente.contas.append(conta)
    
    def transferencia(self, conta1: Conta, conta2: Conta, valor: float):
        if conta1 not in self.contas:
            raise NonCountError(conta1.numero)
        if conta2 not in self.contas:
            raise NonCountError(conta2.numero)
        
        if conta1.debitar(valor):
            conta2.creditar(valor)
            conta1.operacoes.append(Operacao(tipo="Transferencia - Debito", valor=valor))
            conta2.operacoes.append(Operacao(tipo="Transferencia - Credito", valor=valor))
        else:
            raise OperationError("Saldo insuficiente ou outra falha na operação")

    def deposito(self, conta: Conta, valor: float):
        if conta not in self.contas:
            raise NonCountError(conta.numero)
        conta.operacoes.append(Operacao(tipo="Deposito", valor=valor))
        conta.creditar(valor)

    def saque(self, conta: Conta, valor: float):
        if conta not in self.contas:
            raise NonCountError(conta.numero)
        
        if not conta.limite_saque():
            raise OperationError("Limite de saques diários atingido")
        
        if conta.debitar(valor):
            conta.operacoes.append(Operacao(tipo=TipoOperacao.SAQUE, valor=valor))
            conta.saques_diarios += 1
        else:
            raise OperationError("Saldo insuficiente ou outra falha na operação")
        