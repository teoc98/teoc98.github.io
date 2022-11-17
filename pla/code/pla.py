#!/usr/bin/python
# -*- coding: utf-8 -*-
# ======================================================================================================= #
#   
#   $Log: pla.py,v $
#
#  	Revision 3.2  2018/07/11 17:02:23  matteo
#   Eliminati alcuni bug. 
#
#   Revision 3.0  2018/07/10 16:32:51  matteo
#   Il programma è ora compatibile con Python3, oltre che con Python2. 
#
#   Revision 2.1  2012/07/29 15:55:06  alice
#   Il programma è stato reso eseguibile, e dotato di opzioni dalla riga di
#   comando. Sono inoltre state implementate ulteriori dipendenze di parametri
#   dimensionali in modo da rendere il simulatore ancor più ridimensionabile
#   automaticamente sulla base di dimensione orizzontale e numero di I/O/AND.
#
#   Revision 2.0  2012/06/13 14:00:59  alice
#   Commenti adattati al metalinguaggio epytext, per la generazione automatica della
#   documentazione.
#   
#   Revision 1.5  2012/06/08 08:48:55  alice
#   Modificata l'acquisizione della libreria per una massima flessibilità;
#   aggiunti tutti i circuiti disponibili sul testo Tanenbaum e altri.
#   
#   Revision 1.4  2012/06/06 07:54:09  alice
#   Completata l'aggiunta di circuiti da libreria, con possibilità di numero
#   arbitrario di input e output, purché entro quelli del PLA
#   
#   Revision 1.3  2012/04/16 09:52:35  alice
#   Prima versione completa con pulsanti RUN e RESET
#   
#   Revision 1.2  2012/03/30 15:12:02  alice
#   Semplice sistemazione del codice e inserimento commenti, nessuna modifica
#   funzionale
#   
#   Revision 1.1.1.1  2012/02/29 16:41:00  alice
#   Programmable Logic Array simulator
#
# ======================================================================================================= #

"""
Il simulatore di Programmable Logic Array.
@authors: Alice Plebe, Matteo Cavallaro
@version: 3.0

@var sim: istanza base di Tkinter
@var pla: istanza della classe Pla, che contiene il simulatore corrente
"""

from optparse   import OptionParser
from sys import version_info
if version_info[0]==2:
    from Tkinter    import Tk, Frame, Canvas, IntVar
    from Tkinter    import Button, Menubutton, Menu
    from Tkinter    import RIGHT, LEFT, RAISED, NORMAL, HIDDEN
elif version_info[0]==3:
    from tkinter    import Tk, Frame, Canvas, IntVar
    from tkinter    import Button, Menubutton, Menu
    from tkinter    import RIGHT, LEFT, RAISED, NORMAL, HIDDEN
from numpy      import array, empty, zeros
from component  import And, Or, Not, Fuse, Wire, InPin, OutPin
import circuits

class Pla( object ):
    """
    La classe del circuito PLA.
    Comprende i parametri definitori del layout del circuito, include nei suoi attributi le liste
    di tutti gli oggetti di classe Component che costituiscono il circuito.
    
    Un oggetto Pla viene inizializzato con argomento il Tk root widget.
    
    Notare i tre livelli di coordinate che coesistono nel simulatore:
        1. normalizzate [0...1]
        2. assolute [pixel]
        3. in unità di griglia, corrispondente alla distanza fra due fusibili adiacenti uguale nelle
          due dimensioni
    Tutti i tre sistemi di riferimento hanno origine nell'angolo superiore sinistro.

    @cvar debug: livello di debug, dev'essere = 0 in produzione
    @cvar x_size: dimensione in pixel della lunghezza della finestra del simulatore
    @cvar n_inputs: numero di ingressi del circuito, corrispondente al numero di porte NOT
    @cvar n_outputs: numero di uscite del circuito, corrispondente al numero di OR
    @cvar n_and: numero di porte AND
    @cvar title: titolo della finestra in cui è contenuto il simulatore
    @cvar halo: gittata del click nel selezionare fusibili
    @type halo: frazione della lunghezza della finestra
    @cvar l_and: spazio orizzontale dedicato alle AND
    @type l_and: # grid_delta
    @cvar l_or: spazio verticale dedicato alle OR
    @type l_or: # grid_delta
    @cvar upper_block: coordinata verticale del centro delle NOT
    @type upper_block: # grid_delta
    @cvar lower_block: minima spaziatura verticale tra outputs e bordo inferiore
    @type lower_block: # grid_delta
    @cvar grid_cols: numero di colonne virtuali nella Tkinter.grid
    @cvar grid_but_extra: spazio aggiuntivo per il posizionamento del pulsante di run
    @type grid_but_extra: range [1.0-2.0]

    @ivar g_inputs: lista dei componenti grafici della classe Component.InPin istanziati
    @ivar g_outputs: lista dei componenti grafici della classe Component.OutPin istanziati
    @ivar g_and: lista dei componenti grafici della classe Component.Port.And istanziati
    @ivar g_not: lista dei componenti grafici della classe Component.Port.Not istanziati
    @ivar g_or: lista dei componenti grafici della classe Component.Port.Or istanziati
    @ivar g_fuse_in: lista dei componenti grafici della classe Component.Fuse istanziati
    @ivar g_fuse_out: lista dei componenti grafici della classe Component.Fuse istanziati
    @ivar inputs: lista di variabili di classe IntVar usate per gli input
    @ivar n_or: numero di porte OR
    @ivar n_not: numero di porte NOT
    @ivar grid_delta: passo di griglia del layout del circuito
    @ivar a_ratio: aspect ratio della finestra del simulatore
    """

    debug           = 0                     # livello di debug

    usage           = """%prog [-x x_size][-i n_inputs][-o n_outputs][-a n_and]""";


# ------------------------------------------------------------------------------------------------------- #
#   parametri principali del programma
# ------------------------------------------------------------------------------------------------------- #

    x_size          = 800                   # dimensione in pixel della lunghezza della finestra del PLA

    n_inputs        = 6                     # numero di ingressi del circuito
    n_outputs       = 8                     # numero di uscite del circuito, corrispondente al numero di OR
    n_and           = 16                    # numero di porte AND
    title           = 'PLA simulator'

    halo            = 0.025                 # gittata del click nel selezionare fusibili [pixel]
    l_and           = 2.7                   # spazio orizzontale dedicato alle AND [grid_delta]
    l_or            = 1.3                   # spazio verticale dedicato alle OR [grid_delta]
    upper_block     = 3.6                   # coordinata verticale del centro delle NOT [grid_delta]
    lower_block     = 5                     # minima spaziatura verticale tra outputs e bordo inferiore
    grid_cols       = 10                    # numero di colonne virtuali nella Tkinter.grid
    grid_but_extra  = 1.8                   # spazio aggiuntivo per il posizionamento del pulsante di run



# ------------------------------------------------------------------------------------------------------- #
#   parametri derivati, verranno validati dalla __init__()
# ------------------------------------------------------------------------------------------------------- #

# serie di liste che contengono tutti gli oggetti grafici della classe Component 
    g_inputs        = None
    g_outputs       = None
    g_and           = None
    g_not           = None
    g_or            = None
    g_fuse_in       = None
    g_fuse_out      = None

    inputs          = []                    # lista di variabili di classe IntVar usate per gli input

    n_or            = 0                     # numero di porte OR
    n_not           = 0                     # numero di porte NOT
    grid_delta      = 0                     # passo di griglia del layout del circuito
    a_ratio         = 0                     # aspect ratio della finestra del simulatore


# ======================================================================================================= #


    def _layout( self ):
        """
        Calcola diversi parametri derivati per stabilire il layout dei componenti.
        Viene anzitutto definita l'unità di griglia, che può essere la spaziatura minima dei componenti
        in senso orizzontale oppure verticale, in funzione della I{aspec ratio} e del numero di componenti.

        Vengono successivamente stabilite le coordinate fisse dei vari componenti.
        """
        self.n_not          = self.n_inputs
        self.n_or           = self.n_outputs

        l                   = 2 * self.n_inputs + self.n_outputs + self.l_and
        h                   = self.upper_block + ( self.n_and - 1 ) + self.lower_block + self.l_or

        self.a_ratio        = float( l ) / float( h )
        self.size           = ( self.x_size, self.x_size / self.a_ratio )

        d                   = 1.0 / h
        self.grid_delta     = d

        
        self.not_start      = d
        Not.y_not           = d * self.upper_block

        self.inputs_start   = d
        InPin.y_in          = 2 * d

        self.or_start       = d * ( 2 * self.n_inputs + self.l_and )
        Or.y_or             = d * ( self.upper_block + self.n_and + self.l_or + 0.5 )

        self.outputs_start  = d * ( 2 * self.n_inputs + self.l_and )
        OutPin.y_in         = d * ( self.upper_block + self.n_and + self.l_or + 1.5 )

        self.and_start      = d * ( self.upper_block + 1 )
        And.x_and           = d * ( 2 * self.n_inputs + self.l_and / 2 )



    def _m_init( self, o, c ):
        """
        Funzione ausiliaria per inserire nel menu a tendina le descrizioni dei circuiti di libreria.

        @param o: riferimento al menu a tendina
        @type o: Tkinter.Menu
        @param c: circuito da inserire
        @type c: Circuit
        """
        o.add_command( label=c.description, command=lambda x=c : self.load( x ) )


    def _g_init( self ):
        """
        Inizializza i vari NumPy array per ogni categoria di componente.
        """
        self.g_and      = empty( self.n_and, dtype=object )
        self.g_not      = empty( self.n_not, dtype=object )
        self.g_or       = empty( self.n_or, dtype=object )
        self.g_inputs   = empty( self.n_inputs, dtype=object )
        self.g_outputs  = empty( self.n_outputs, dtype=object )

        c               = 2 * self.n_not
        r               = self.n_and
        self.g_fuse_in  = empty( ( r, c ), dtype=object )

        c               = self.n_or
        r               = self.n_and
        self.g_fuse_out = empty( ( r, c ), dtype=object )


    
    def __init__( self, root ):
        """
        Inizializza il Programmable Logic Array

        @param root: la Tk root widget
        @type root: Tkinter object
        """
        self._layout()

        root.title( self.title )
        self.root       = root

        w, h            = self.size
        self.canvas     = Canvas( root, height=h, width=w )
        self.canvas.grid( row=0, column=0, rowspan=3, columnspan=self.grid_cols )

        # menubar
        self.menubar	= Menu( root )

        menu_b		= Menu( self.menubar, tearoff=0 )
        self.menubar.add_cascade( label="Simulation", menu=menu_b )
        menu_b.add_command( label="Fuse all", command=self.fuse_all, accelerator="F" )
        menu_b.add_command( label="Unfuse all", command=self.reset, accelerator="U" )
        menu_b.add_command( label="Quit", command=self.root.quit, accelerator="Q" )
        menu_b		= Menu( self.menubar, tearoff=0 )
        self.menubar.add_cascade( label="Library", menu=menu_b )
        for c in circuits.circs:
            self._m_init( menu_b, c )
        try:
            self.root.config( menu=self.menubar )
        except AttributeError:
            self.root.tk.call( root, "config", "-menu", self.menubar )

        # pulsanti
        n_i2            = 2 * self.n_inputs
        n_tot           = int( ( n_i2 + self.n_outputs ) * self.grid_but_extra )
        col             = self.grid_cols * int(n_i2 / n_tot)
        self.b_run      = Button( root, text='RUN', width=10, command=self.run )
        self.b_run.grid( row=2, column=col )

        self.inputs     = [ IntVar( root ) for i in range( self.n_inputs ) ]

        self._g_init()

        self.root.bind( "<KeyPress-q>", self._event_q )
        self.root.bind( "<KeyPress-Q>", self._event_q )
        self.root.bind( "<KeyPress-f>", self._event_f )
        self.root.bind( "<KeyPress-F>", self._event_f )
        self.root.bind( "<KeyPress-u>", self._event_u )
        self.root.bind( "<KeyPress-U>", self._event_u )
        self.root.bind( "<KeyPress-r>", self._event_r )
        self.root.bind( "<KeyPress-R>", self._event_r )

        



    def nor_to_abs( self, n ):
        """
        Converte coordinate normalizzate in dimensioni assolute.

        @note: la conversione si basa solamente sulla dimensione verticale.
        @param n: coordinata iniziale
        @type n: dimensione normalizzata 0..1
        @return: coordinata in dimensioni assolute [pixel]
        """
        return int( self.size[ 1 ] * n )


# ======================================================================================================= #


    def add_and( self, y ):
        """
        Crea una porta AND e aggiunge l'oggetto grafico nell'array corrispondente.

        @param y: coordinata verticale del centro della porta
        @type y: dimensione normalizzata 0..1
        """
        self.g_and[ And.count - 1 ] = And( self, y )

    def place_and( self ):
        """
        Crea tutte le porte AND nelle posizioni stabilite dal layout.
        """
        y   = self.and_start
        dy  = self.grid_delta

        for i in range( self.n_and ):
            self.add_and( y )
            y += dy



    def add_or( self, x ):
        """
        Crea una porta OR e aggiunge l'oggetto grafico nell'array corrispondente.

        @param x: coordinata orizzontale del centro della porta
        @type x: dimensione normalizzata 0..1
        """
        self.g_or[ Or.count - 1 ] = Or( self, x )

    def place_or( self ):
        """
        Crea tutte le porte OR nelle posizioni stabilite dal layout.
        """
        x   = self.or_start
        dx  = self.grid_delta

        for i in range( self.n_or ):
            self.add_or( x )
            x += dx



    def add_not( self, x ):
        """
        Crea una porta NOT e aggiunge l'oggetto grafico nell'array corrispondente.

        @param x: coordinata orizzontale del centro della porta
        @type x: dimensione normalizzata 0..1
        """
        self.g_not[ Not.count - 1 ] = Not( self, x )

    def place_not( self ):
        """
        Crea tutte le porte NOT nelle posizioni stabilite dal layout.
        """
        x   = self.not_start
        dx  = 2 * self.grid_delta

        for i in range( self.n_not ):
            self.add_not( x )
            x += dx


# ------------------------------------------------------------------------------------------------------- #


    def place_inputs( self ):
        """
        Crea tutti i pin di input e conserva gli oggetti grafici negli array.
        Genera inoltre i relativi collegamenti con le porte NOT.
        """
        x   = self.inputs_start
        dx  = 2 * self.grid_delta

        x += dx / 2
        for i in range( self.n_inputs ):
            inpin		= InPin( self, x, self.inputs[ i ] )
            inpin.wire_not( self, self.g_not[ i ] )
            self.g_inputs[ i ]  = inpin
            x += dx


    def place_outputs( self ):
        """
        Crea tutti i pin di output e conserva gli oggetti grafici negli array.
        Genera inoltre i relativi collegamenti con le porte OR.
        """
        x   = self.outputs_start
        dx  = self.grid_delta

        for i in range( self.n_outputs ):
            outpin              = OutPin( self, x )
            self.g_outputs[ i ] = outpin
            Wire( self, self.g_or[ i ], outpin )
            x += dx


# ------------------------------------------------------------------------------------------------------- #


    def place_wire_in( self ):
        """
        Realizza i collegamenti tra i fusibili nella matrice di collegamenti tra input e porte AND.
        """
        for r in range( self.n_and ):
            for c in range( 2 * self.n_not - 1 ):
                Wire( self, self.g_fuse_in[ r, c ], self.g_fuse_in[ r, c + 1 ] )
            Wire( self, self.g_fuse_in[ r, 2 * self.n_not - 1 ], self.g_and[ r ] )

        for c in range( self.n_not ):
            Wire( self, self.g_not[ c ], self.g_fuse_in[ self.n_and - 1, 2 * c ],
                    placement=( 'pin', 'center' ) )

        for c in range( self.n_inputs ):
            Wire( self, self.g_inputs[ c ], self.g_fuse_in[ self.n_and - 1, 2 * c + 1 ],
                    placement=( 'pin', 'center' ) )


    def place_wire_out( self ):
        """
        Realizza i collegamenti tra i fusibili nella matrice di collegamenti tra porte AND e OR.
        """
        for r in range( self.n_and ):
            Wire( self, self.g_and[ r ], self.g_fuse_out[ r, 0 ] )
            for c in range( self.n_or - 1 ):
                Wire( self, self.g_fuse_out[ r, c ], self.g_fuse_out[ r, c + 1 ] )

        for c in range( self.n_or ):
            Wire( self, self.g_fuse_out[ 0, c ], self.g_or[ c ], placement=( 'center', 'pin' ) )


# ------------------------------------------------------------------------------------------------------- #


    def _get_fuse_in( self, tag ):
        """
        Restituisce l'oggetto grafico del fusibile corrispondente ad un I{tag},
        appartenente alla matrice IN-AND.

        @param tag: il tag del fusibile.
        """
        l   = len( 'fuse_in_' )
        n   = int( tag[ l : ] )
        r   = n // ( self.n_not * 2 )
        c   = n % ( self.n_not * 2 )
        return self.g_fuse_in[ r, c ]

    def place_fuse_in( self ):
        """
        Crea i fusibili relativi alla matrice IN-AND.
        """
        x   = self.not_start
        dx  = self.grid_delta
        y   = self.and_start
        dy  = self.grid_delta

        for r in range( self.n_and ):
            x   = self.not_start
            for c in range( 2 * self.n_not ):
                self.g_fuse_in[ r, c ] = Fuse( self, x, y, 'in_' )
                x += dx
            y += dy




    def _get_fuse_out( self, tag ):
        """
        Restituisce l'oggetto grafico del fusibile corrispondente ad un I{tag},
        appartenente alla matrice AND-OR.

        @param tag: il tag del fusibile.
        """
        l   = len( 'fuse_out_' )
        n   = int( tag[ l : ] )
        r   = n // self.n_or
        c   = n % self.n_or
        return self.g_fuse_out[ r, c ]

    def place_fuse_out( self ):
        """
        Crea i fusibili relativi alla matrice AND-OR.
        """
        x   = self.or_start
        dx  = self.grid_delta
        y   = self.and_start
        dy  = self.grid_delta

        for r in range( self.n_and ):
            x   = self.or_start
            for c in range( self.n_or ):
                self.g_fuse_out[ r, c ] = Fuse( self, x, y, 'out_' )
                x += dx
            y += dy


# ======================================================================================================= #


    def switch_fuse_in( self, tag ):
        """
        Realizza lo switch di un fusibile della matrice IN-AND.

        @param tag: il tag del fusibile.
        """
        f   = self._get_fuse_in( tag )
        f.toggle( self )

    def switch_fuse_out( self, tag ):
        """
        Realizza lo switch di un fusibile della matrice AND-OR.

        @param tag: il tag del fusibile.
        """
        f   = self._get_fuse_out( tag )
        f.toggle( self )



    def get_tag( self, x, y, comp=None ):
        """
        Cerca il componente più vicino alla coordinata specificata, e ne restituisce il I{tag}.

        Se viene specificato l'argomento I{comp} la ricerca è limitata a quel tipo di componente
        i componenti vengono rilevati in un intervallo rettangolare di dimensioni \I{halo}.

        @param x: coordinata orizzontale del punto di inizio della ricerca
        @param y: coordinata verticale del punto di inizio della ricerca
        @param comp: categoria di componente a cui viene limitata la ricerca
        @type comp: Component
        """
        halo	= self.halo * self.x_size
        x0      = x - halo
        x1      = x + halo
        y0      = y - halo
        y1      = y + halo
        ids     = self.canvas.find_overlapping( x0, y0, x1, y1 )

        fl      = lambda x: len( self.canvas.gettags( x ) )
        ids     = list(filter( fl, ids ))
        if comp is not None:
            fl      = ( lambda x: comp in self.canvas.gettags( x )[ 0 ] )
            ids     = list(filter( fl, ids ))

        if not len( ids ):
            return None
        return self.canvas.gettags( ids[ 0 ] )[ 0 ]



    def _event_q( self, event ):
        """
        Gestore della I{shortcut} da tastiera "q"/"Q".

        @param event: evento catturato da Tkinter.bind, non utilizzato
        @type event: instance
        """
        self.root.quit()
        exit()

    def _event_f( self, event ):
        """
        Gestore della I{shortcut} da tastiera "f"/"F".

        @param event: evento catturato da Tkinter.bind, non utilizzato
        @type event: instance
        """
        self.fuse_all()

    def _event_u( self, event ):
        """
        Gestore della I{shortcut} da tastiera "u"/"U".

        @param event: evento catturato da Tkinter.bind, non utilizzato
        @type event: instance
        """
        self.reset()

    def _event_r( self, event ):
        """
        Gestore della I{shortcut} da tastiera "r"/"R".

        @param event: evento catturato da Tkinter.bind, non utilizzato
        @type event: instance
        """
        self.run()



    def handler( self, event ):
        """
        Identifica il componente su cui si è cliccato e esegue l'opportuna operazione.

        Tipicamente viene alternato lo stato di un fusibile.

        @param event: evento catturato da Tkinter.bind, utilizzato per identificare la posizione del mouse
        @type event: instance
        """
        t   = self.get_tag( event.x, event.y, 'fuse' )

        if self.debug > 2:
            print(event.x, event.y, ': ', t)

        if t is None:
            return
        if 'fuse_in' in t:
            return self.switch_fuse_in( t )
        if 'fuse_out' in t:
            return self.switch_fuse_out( t )



    def place_components( self ):
        """
        Posiziona l'intero set di componenti nel layout, e avvia la gestione del mouse.
        """
        self.place_and()
        self.place_or()
        self.place_not()
        self.place_inputs()
        self.place_outputs()
        self.place_fuse_in()
        self.place_fuse_out()
        self.place_wire_in()
        self.place_wire_out()

        self.canvas.bind( "<Button-1>", self.handler )



# ======================================================================================================= #
#
#       controllo della parte logica
#
# ======================================================================================================= #

    def compute_and( self, r ):
        """
        Computa la funzione di una porta logica AND.

        @param r: la riga di fusibili a cui è legata la porta.
        """
        default     = False
        fuses       = self.g_fuse_in[ r ]

        for k in range( self.n_inputs ):
            f       = fuses[ 2 * k ].status
            i       = self.g_inputs[ k ].var.get()
            if ( f and i ):
                return False
            if ( f and not i ):
                default = True

        for k in range( self.n_inputs ):
            f       = fuses[ 2 * k + 1].status
            i       = self.g_inputs[ k ].var.get()
            if ( f and not i ):
                return False
            if ( f and i ):
                default = True

        return default


    def compute_ands( self ):
        """
        Calcola gli output ottenuti dalle porte AND.
        """
        for i in range( self.n_and ):
            self.g_and[ i ].value( self, self.compute_and( i ) )



    def compute_out( self, c ):
        """
        Computa la funzione di una porta logica OR.

        @param c: la colonna di fusibili a cui è legata la porta.
        """
        fuses       = self.g_fuse_out[ :, c ]

        for k in range( self.n_and ):
            f       = fuses[ k ].status
            a       = self.g_and[ k ].status
            if ( f and a ):          # il solo caso in cui la OR e` vera
                return True

        return False


    def compute_outs( self ):
        """
        Calcola gli output ottenuti dalle porte OR, e quindi dell'intero PLA.
        """
        for i in range( self.n_outputs ):
            self.g_outputs[ i ].value( self, self.compute_out( i ) )



    def run( self ):
        """
        Avvia la computazione dell'output del PLA.
        """
        self.compute_ands()
        self.compute_outs()



# ======================================================================================================= #


    def fuse_all( self ):
        """
        Resetta i componenti grafici come al momento di avvio del programma,
        con i fusibili tutti non collegati.
        """
        for i in range( self.n_inputs ):
            self.g_inputs[ i ].reset( self )

        for i in range( self.n_and ):
            self.g_and[ i ].reset( self )

        for i in range( self.n_outputs ):
            self.g_outputs[ i ].reset( self )

        for r in range( self.n_and ):
            for c in range( 2 * self.n_inputs ):
                self.g_fuse_in[ r, c ].deset( self )

        for r in range( self.n_and ):
            for c in range( self.n_outputs ):
                self.g_fuse_out[ r, c ].deset( self )


    def reset( self ):
        """
        Resetta i componenti grafici come al momento di avvio del programma,
        con i fusibili tutti collegati.
        """
        for i in range( self.n_inputs ):
            self.g_inputs[ i ].reset( self )

        for i in range( self.n_and ):
            self.g_and[ i ].reset( self )

        for i in range( self.n_outputs ):
            self.g_outputs[ i ].reset( self )

        for r in range( self.n_and ):
            for c in range( 2 * self.n_inputs ):
                self.g_fuse_in[ r, c ].reset( self )

        for r in range( self.n_and ):
            for c in range( self.n_outputs ):
                self.g_fuse_out[ r, c ].reset( self )


# ======================================================================================================= #


    def load( self, circ ):
        """
        Carica uno dei circuiti disponibili in libreria.

        @param circ: circuito da caricare
        @type circ: Circuit
        """
        if circ.n_inputs > self.n_inputs:
            print("non ci sono abbastanza input disponibili per caricare questo circuito")
            return

        if circ.n_and > self.n_and:
            print("non ci sono abbastanza porte AND disponibili per caricare questo circuito")
            return

        if circ.n_outputs > self.n_outputs:
            print("non ci sono abbastanza output disponibili per caricare questo circuito")
            return

        self.fuse_all()

        # matrice fuse sinistra
        for r in range( circ.n_and ):
            for c in range( 2 * circ.n_inputs ):
                if circ.and_matrix[ r, c ]:
                    self.g_fuse_in[ r, c ].reset( self )
                else:
                    self.g_fuse_in[ r, c ].deset( self )

        # matrice fuse destra
        for r in range( circ.n_and ):
            for c in range( circ.n_outputs ):
                if circ.or_matrix[ r, c ]:
                    self.g_fuse_out[ r, c ].reset( self )
                else:
                    self.g_fuse_out[ r, c ].deset( self )

        # array porte and
        for i in range( circ.n_and, self.n_and ):
            self.g_and[ i ].disable( self )

        # array inputs
        for i in range( circ.n_inputs ):
            self.g_inputs[ i ].set_label( self, circ.labels_i[ i ] )
        for i in range( circ.n_inputs, self.n_inputs ):
            self.g_inputs[ i ].disable()

        # array outputs
        for i in range( circ.n_outputs ):
            self.g_outputs[ i ].set_label( self, circ.labels_o[ i ] )
        for i in range( circ.n_outputs, self.n_outputs ):
            self.g_outputs[ i ].disable( self )


# ======================================================================================================= #

def options( a ):
    """
    Definisce le opzioni accettate dal programma nella linea di comando.
    Questa funzione utilizza il metodo OptionParser.add_option() per specificare gli
    attributi di tutte le optioni accettate dal programma

    @param a: istanza di OptionParser
    @type a: oggetto OptionParser
    """
    a.add_option( "-x",
            action  = "store",
            type    = "int",
            nargs   = 1,
            dest    = "x_size",
            metavar = "<x_size>",
            help    = "dimensione orizzontale della finestra [pixel]",
            default = Pla.x_size
    )
    a.add_option( "-i",
            action  = "store",
            type    = "int",
            nargs   = 1,
            dest    = "n_inputs",
            metavar = "<n_inputs>",
            help    = "numero di pin di ingresso",
            default = Pla.n_inputs
    )
    a.add_option( "-o",
            action  = "store",
            type    = "int",
            nargs   = 1,
            dest    = "n_outputs",
            metavar = "<n_outputs>",
            help    = "numero di pin di uscita",
            default = Pla.n_outputs
    )
    a.add_option( "-a",
            action  = "store",
            type    = "int",
            nargs   = 1,
            dest    = "n_and",
            metavar = "<n_and>",
            help    = "numero di porte AND",
            default = Pla.n_and
    )

args            = OptionParser( Pla.usage )
options( args )
( opts, more )  = args.parse_args()
Pla.x_size      = opts.x_size
Pla.n_inputs    = opts.n_inputs
Pla.n_outputs   = opts.n_outputs
Pla.n_and       = opts.n_and

sim             = Tk()
pla             = Pla( sim )
sim.attributes( '-topmost', 1 )     # per porre la finestra in primo piano
pla.place_components()
sim.mainloop()
